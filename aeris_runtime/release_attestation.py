"""Production tooling for the formal four-way release-attestation mechanism
defined in release_evidence.py.

This module only computes objective facts (the version tuple), assembles the
task/Evidence that both signers attest against, and lets a principal sign
with *its own* key. It never signs on behalf of a principal it does not
control, and it never fabricates the Human Chief Engineer's approval --
`release_evidence.py`'s own G5 gate check requires `kind == "HUMAN"`, and no
automated process in this codebase is permitted to self-certify that (see
docs/AERIS_P3_GOLDEN_ENGINEER.md's stance on L2->L3 promotion, which the same
principle traces back to). The AI-held "implementer" key below is legitimate
to auto-provision -- it represents AERIS's own operating identity, distinct
from and never substituting for the Human's own reviewer key.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import audit, evidence, taskstate
from .audit import append_event
from .blueprint_compatibility import TARGET as CORE_TARGET
from .config import ROOT, load_config
from . import release_evidence as auth

RELEASE_SCOPE = "FORMAL_RELEASE_ATTESTATION"
RELEASE_ARTIFACT_ID = "AERIS_VERSION_TUPLE"
IMPLEMENTER_SUBJECT_ID = "AERIS_LOCAL_IMPLEMENTATION"
IMPLEMENTER_CONTEXT = "aeris_runtime_automated_release_preparation"
IMPLEMENTER_SIGNER_ID = "aeris-implementer"
IMPLEMENTER_KEY_FILE = ROOT / ".aeris" / "authority" / "implementer.key"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True, timeout=10).strip()


def _worktree_dirty() -> bool:
    return bool(_git("status", "--porcelain", "--untracked-files=no"))


def _tracked_tree_digest(rel_dir: str) -> str:
    """Sha256 over sorted (path, file-sha256) pairs for every *tracked* file
    under rel_dir (via `git ls-files`, so local scratch/cache files never
    affect it) -- used to detect on-disk drift in that subtree."""
    listing = _git("ls-files", rel_dir)
    entries = []
    for rel in sorted(listing.splitlines()):
        path = ROOT / rel
        if path.is_file():
            entries.append([rel, hashlib.sha256(path.read_bytes()).hexdigest()])
    return hashlib.sha256(auth.canonical(entries)).hexdigest()


def configuration_digest() -> str:
    config = load_config()
    payload = {"mode": config.mode, "local_network_scope": config.local_network_scope}
    return hashlib.sha256(auth.canonical(payload)).hexdigest()


def asset_digest() -> str:
    return _tracked_tree_digest("ui/web")


def _last_supervisor_start() -> str | None:
    # Read audit.LEDGER_PATH fresh here, not via a bound module-load-time
    # import -- see audit.py's own comment on why: a bound copy would not
    # see patch.object(audit, "LEDGER_PATH", ...) from test isolation.
    ledger_path = audit.LEDGER_PATH
    if not ledger_path.exists():
        return None
    for line in reversed(ledger_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("event_type") == "SUPERVISOR_STARTED":
            return record.get("timestamp_utc")
    return None


def compute_version_tuple() -> dict[str, Any]:
    """The objective, unsigned facts every signer attests against. Fails
    closed (raises) rather than guessing when the checkout is dirty or no
    supervisor start has ever been observed -- an honest 'not ready to
    attest yet' beats a fabricated version tuple."""
    if _worktree_dirty():
        raise ValueError("cannot attest a release from a dirty worktree; commit or stash first")
    sha = _git("rev-parse", "HEAD")
    started_at = _last_supervisor_start()
    if started_at is None:
        raise ValueError("no SUPERVISOR_STARTED audit event found; start AERIS at least once before attesting")
    now = datetime.now(timezone.utc)
    config_digest = configuration_digest()
    asset_dig = asset_digest()
    return {
        "core_blueprint": {"repository": "Space653000/0_JN1_AERIS", "commit_sha": CORE_TARGET},
        "implementation": {"repository": "Space653000/0_JN1_AERIS_Local-computer-implementation", "commit_sha": sha},
        "local_checkout": {
            "commit_sha": sha, "dirty": False,
            "overlay_digest": _tracked_tree_digest("config"),
            "configuration_digest": config_digest,
            "asset_digest": asset_dig,
        },
        "running_service": {
            "implementation_sha": sha, "core_sha": CORE_TARGET,
            "configuration_digest": config_digest, "asset_digest": asset_dig,
            "started_at": started_at, "observed_at": now.isoformat(),
        },
    }


def _implementer_key() -> bytes:
    """AERIS's own operating key for signing its own implementer attestation
    -- auto-provisioned once, analogous to the supervisor token file. This is
    NOT the Human's reviewer key and can never satisfy the G5 gate alone
    (release_evidence.resolve() requires a *different* principal of
    kind=='HUMAN' for that)."""
    IMPLEMENTER_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if IMPLEMENTER_KEY_FILE.is_file():
        return bytes.fromhex(IMPLEMENTER_KEY_FILE.read_text(encoding="utf-8").strip())
    key = secrets.token_bytes(32)
    IMPLEMENTER_KEY_FILE.write_text(key.hex(), encoding="utf-8")
    return key


def _load_trust() -> dict[str, Any]:
    if auth.TRUST_STORE.is_file():
        return json.loads(auth.TRUST_STORE.read_text(encoding="utf-8"))
    return {"principals": {}}


def _save_trust(trust: dict[str, Any]) -> None:
    auth.TRUST_STORE.parent.mkdir(parents=True, exist_ok=True)
    auth.TRUST_STORE.write_text(json.dumps(trust, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_implementer_principal() -> None:
    trust = _load_trust()
    trust.setdefault("principals", {})[IMPLEMENTER_SIGNER_ID] = {
        "key_hex": _implementer_key().hex(),
        "revoked": False,
        "subject_id": IMPLEMENTER_SUBJECT_ID,
        "kind": "IMPLEMENTER",
        "can_implement": True,
        "execution_contexts": [IMPLEMENTER_CONTEXT],
    }
    _save_trust(trust)


def prepare_release_task() -> dict[str, Any]:
    """Create the task + sealed Evidence bundle the release attests, and
    sign AERIS's own implementer attestation for it. Returns everything the
    Human needs to mint their own G5 approval receipt afterward -- this
    function stops there; it never signs the reviewer/G5 side."""
    ensure_implementer_principal()
    versions = compute_version_tuple()
    version_tuple_sha256 = hashlib.sha256(auth.canonical(versions)).hexdigest()
    artifact_bytes = auth.canonical(versions)
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()

    metadata = {
        "scope": RELEASE_SCOPE,
        "artifact_id": RELEASE_ARTIFACT_ID,
        "artifact_sha256": artifact_sha256,
        "implementer_id": IMPLEMENTER_SUBJECT_ID,
        "implementer_context": IMPLEMENTER_CONTEXT,
        "version_tuple_sha256": version_tuple_sha256,
        "implementer_attestation_ref": "IMPLEMENTER_ATTESTATION",
    }
    task = taskstate.create_task(
        f"Formal release attestation for {versions['implementation']['commit_sha'][:12]}",
        "AERIS Supervisor", risk="R4", metadata=metadata,
    )
    bundle = evidence.create_bundle(task["task_id"], IMPLEMENTER_SUBJECT_ID)
    run_id = bundle["run_id"]
    root = evidence.bundle_dir(run_id)
    (root / "version_tuple.json").write_text(json.dumps(versions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "processed" / "release-artifact.bin").write_bytes(artifact_bytes)
    seal = evidence.seal_bundle(run_id, "AERIS Supervisor")
    bundle_sha256 = hashlib.sha256((root / "bundle_manifest.json").read_bytes()).hexdigest()

    now = datetime.now(timezone.utc)
    # Freshness window is bounded by release_evidence.MAX_AGE_SECONDS (24h);
    # give the Human nearly a full day from right now to mint their G5 receipt.
    expires_at = (now + timedelta(hours=23, minutes=59)).isoformat()
    implementer_payload = {
        "type": auth.IMPLEMENTER_PURPOSE,
        "signer_id": IMPLEMENTER_SIGNER_ID,
        "task_id": task["task_id"],
        "scope": metadata["scope"],
        "artifact_id": metadata["artifact_id"],
        "artifact_sha256": metadata["artifact_sha256"],
        "implementer_id": metadata["implementer_id"],
        "implementer_context": metadata["implementer_context"],
        "version_tuple_sha256": metadata["version_tuple_sha256"],
        "run_id": run_id,
        "bundle_sha256": bundle_sha256,
        "issued_at": now.isoformat(),
        "expires_at": expires_at,
    }
    implementer_receipt = {
        "payload": implementer_payload,
        "signature": hmac.new(_implementer_key(), auth.canonical(implementer_payload), hashlib.sha256).hexdigest(),
    }
    auth.RECEIPTS.mkdir(parents=True, exist_ok=True)
    (auth.RECEIPTS / "IMPLEMENTER_ATTESTATION.json").write_text(json.dumps(implementer_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    append_event("RISK_AUTHORITY_DECISION", "AERIS Supervisor", {
        "task_id": task["task_id"], "run_id": run_id, "scope": metadata["scope"],
        "note": "implementer attestation signed; awaiting Human G5 approval",
    })
    return {
        "task": task, "task_id": task["task_id"], "run_id": run_id, "metadata": metadata,
        "version_tuple_sha256": version_tuple_sha256, "gate": "G5_APPROVAL",
    }


def current_release_authority_status() -> dict[str, Any]:
    """What review.py's independent_acceptance() reports for four_way_aligned
    -- honestly False with a reason until the Human has minted a real G5
    receipt for the *current* implementation_sha, never fabricated."""
    trust_path = auth.TRUST_STORE
    if not trust_path.is_file():
        return {"aligned": False, "reason": "NO_RELEASE_AUTHORITY_TRUST_STORE_CONFIGURED"}
    receipt_path = auth.RECEIPTS / "G5_APPROVAL.json"
    if not receipt_path.is_file():
        return {"aligned": False, "reason": "NO_HUMAN_G5_APPROVAL_RECEIPT_PRESENT"}
    try:
        task_id = json.loads(receipt_path.read_text(encoding="utf-8"))["payload"]["task_id"]
        task = taskstate.load_task(task_id)
        resolved = auth.resolve("G5_APPROVAL", task, "G5_APPROVAL")
    except Exception as exc:
        return {"aligned": False, "reason": f"G5_RECEIPT_DID_NOT_RESOLVE: {exc}"}
    return {"aligned": True, "reason": "G5_APPROVAL_RESOLVED", "authority": resolved.get("_resolved_authority")}
