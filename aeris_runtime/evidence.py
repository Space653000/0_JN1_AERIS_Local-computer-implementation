"""AERIS Evidence Bundle baseline with hashes and provenance.

The baseline provides deterministic manifests and tamper detection for bundle
contents. It does not claim filesystem immutability/WORM semantics.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .audit import append_event
from .config import ROOT

EVIDENCE_ROOT = ROOT / ".aeris" / "evidence"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=5).strip()
    except Exception:
        return "UNKNOWN"


def _core_sha() -> str:
    try:
        return str(json.loads((ROOT / "core.lock.json").read_text(encoding="utf-8-sig"))["baseline_sha"])
    except Exception:
        return "UNKNOWN"


def _safe_run_id(run_id: str) -> str:
    allowed = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in run_id.strip())
    if not allowed or allowed in {".", ".."}:
        raise ValueError("invalid run_id")
    return allowed[:140]


def bundle_dir(run_id: str) -> Path:
    return EVIDENCE_ROOT / _safe_run_id(run_id)


def create_bundle(
    task_id: str,
    actor: str,
    *,
    run_id: str | None = None,
    input_paths: Iterable[Path | str] | None = None,
    requirement_snapshot: dict[str, Any] | None = None,
    method_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_id = _safe_run_id(run_id or f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}")
    root = bundle_dir(run_id)
    if root.exists():
        raise FileExistsError(f"evidence bundle exists: {run_id}")
    for name in ["raw", "processed", "plots"]:
        (root / name).mkdir(parents=True, exist_ok=True)

    inputs: list[dict[str, Any]] = []
    for item in input_paths or []:
        source = Path(item).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        target = root / "raw" / source.name
        if target.exists():
            target = root / "raw" / f"{uuid.uuid4().hex[:8]}-{source.name}"
        shutil.copy2(source, target)
        inputs.append({"source_name": source.name, "stored": str(target.relative_to(root)), "bytes": target.stat().st_size, "sha256": _sha256(target)})

    created = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "task_id": task_id,
        "created_by": actor,
        "created_at_utc": created,
        "implementation_sha": _git_sha(),
        "canonical_core_sha": _core_sha(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pid": os.getpid(),
        "state": "DRAFT",
        "truth": "bundle hash integrity is application evidence; not WORM storage or external attestation",
    }
    (root / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "input_manifest.json").write_text(json.dumps({"inputs": inputs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "requirement_snapshot.json").write_text(json.dumps(requirement_snapshot or {}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "method_snapshot.json").write_text(json.dumps(method_snapshot or {}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "validation.json").write_text(json.dumps({"state": "NOT_VALIDATED", "checks": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_event("EVIDENCE_BUNDLE_CREATED", actor, {"run_id": run_id, "task_id": task_id, "path": str(root)})
    return {"run_id": run_id, "task_id": task_id, "path": str(root), "inputs": inputs}


def _iter_bundle_files(root: Path) -> list[Path]:
    excluded = {"bundle_manifest.json", "checksums.sha256"}
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name not in excluded and not p.is_symlink())


def seal_bundle(run_id: str, actor: str) -> dict[str, Any]:
    root = bundle_dir(run_id)
    if not root.is_dir():
        raise FileNotFoundError(root)
    files = []
    for path in _iter_bundle_files(root):
        files.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "sealed_by": actor,
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "scope": "application_hash_manifest_not_worm_or_external_signature",
    }
    (root / "bundle_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checksum_lines = [f"{item['sha256']}  {item['path']}" for item in files]
    (root / "checksums.sha256").write_text("\n".join(checksum_lines) + ("\n" if checksum_lines else ""), encoding="utf-8")
    append_event("EVIDENCE_BUNDLE_SEALED", actor, {"run_id": run_id, "file_count": len(files)})
    return manifest


def validate_bundle(run_id: str) -> dict[str, Any]:
    root = bundle_dir(run_id)
    manifest_path = root / "bundle_manifest.json"
    if not manifest_path.is_file():
        return {"valid": False, "run_id": run_id, "errors": ["bundle is not sealed"]}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"valid": False, "run_id": run_id, "errors": [f"manifest unreadable: {exc}"]}
    errors: list[str] = []
    expected = {str(item["path"]): item for item in manifest.get("files", [])}
    actual_files = {p.relative_to(root).as_posix(): p for p in _iter_bundle_files(root)}
    missing = sorted(set(expected) - set(actual_files))
    extra = sorted(set(actual_files) - set(expected))
    for rel in missing:
        errors.append(f"missing: {rel}")
    for rel in extra:
        errors.append(f"unhashed extra file: {rel}")
    for rel in sorted(set(expected) & set(actual_files)):
        path = actual_files[rel]
        if _sha256(path) != str(expected[rel].get("sha256", "")):
            errors.append(f"checksum mismatch: {rel}")
    return {
        "valid": not errors,
        "run_id": run_id,
        "files": len(expected),
        "errors": errors,
        "scope": "application_hash_manifest_not_worm_or_external_signature",
    }
