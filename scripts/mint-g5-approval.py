#!/usr/bin/env python3
"""Sign the Human Chief Engineer's G5 formal release approval for a task
prepared by prepare-release-attestation.py, using YOUR OWN key from
authority-keygen.py.

This is the one action in the whole release-attestation mechanism that must
be a real, deliberate decision by an actual human -- nothing in
aeris_runtime signs this on your behalf, and release_evidence.py's own G5
gate check rejects a receipt whose principal is not registered kind=='HUMAN'
with human_authority=='Human Chief Engineer'.

Usage:
    python scripts/mint-g5-approval.py \\
        --key-file .aeris/authority/your-name.key \\
        --signer-id your-name \\
        --task-id AERIS-20260913T...-xxxxxxxx
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aeris_runtime import evidence, release_evidence as auth, taskstate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--key-file", required=True, help="Path to your own key file from authority-keygen.py.")
    parser.add_argument("--signer-id", required=True, help="Your trust-store signer_id from authority-keygen.py.")
    parser.add_argument("--task-id", required=True, help="The task_id printed by prepare-release-attestation.py.")
    args = parser.parse_args()

    key_path = Path(args.key_file)
    if not key_path.is_file():
        print(f"Key file not found: {key_path}", file=sys.stderr)
        return 1
    key = bytes.fromhex(key_path.read_text(encoding="utf-8").strip())

    if not auth.TRUST_STORE.is_file():
        print("No trust store found. Run scripts/authority-keygen.py --human first.", file=sys.stderr)
        return 1
    trust = json.loads(auth.TRUST_STORE.read_text(encoding="utf-8"))
    principal = trust.get("principals", {}).get(args.signer_id)
    if not principal:
        print(f"signer_id {args.signer_id!r} is not in the trust store.", file=sys.stderr)
        return 1
    if principal.get("kind") != "HUMAN" or principal.get("human_authority") != "Human Chief Engineer":
        print("This signer is not registered as the Human Chief Engineer.", file=sys.stderr)
        print("Re-run authority-keygen.py with --human to register that role.", file=sys.stderr)
        return 1

    task = taskstate.load_task(args.task_id)
    metadata = task["metadata"]
    run_id = None
    # The run_id lives in the implementer receipt this task's attestation
    # was prepared with -- re-derive it rather than asking the human to
    # retype it, since it must match exactly.
    implementer_receipt_path = auth.RECEIPTS / f"{metadata['implementer_attestation_ref']}.json"
    if implementer_receipt_path.is_file():
        run_id = json.loads(implementer_receipt_path.read_text(encoding="utf-8"))["payload"]["run_id"]
    if not run_id:
        print("Could not find the implementer attestation for this task. Re-run prepare-release-attestation.py.", file=sys.stderr)
        return 1

    bundle_sha256 = hashlib.sha256((evidence.bundle_dir(run_id) / "bundle_manifest.json").read_bytes()).hexdigest()
    now = datetime.now(timezone.utc)
    isolated_contexts = principal.get("isolated_contexts") or []
    reviewer_context = isolated_contexts[0] if isolated_contexts else f"{args.signer_id}_review_context"

    payload = {
        **metadata,
        "task_id": args.task_id,
        "gate": "G5_APPROVAL",
        "decision": "PASS",
        "signer_id": args.signer_id,
        "reviewer_context": reviewer_context,
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=23, minutes=59)).isoformat(),
        "approval_action": "APPROVE_EXACT_ARTIFACT",
        "run_id": run_id,
        "bundle_sha256": bundle_sha256,
    }
    receipt = {"payload": payload, "signature": hmac.new(key, auth.canonical(payload), hashlib.sha256).hexdigest()}
    auth.RECEIPTS.mkdir(parents=True, exist_ok=True)
    (auth.RECEIPTS / "G5_APPROVAL.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"G5 approval signed and saved for task {args.task_id}.")
    print("Run `python -m aeris_runtime review` (or check /api/v1 acceptance reporting)")
    print("to confirm four_way_aligned now reports true.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
