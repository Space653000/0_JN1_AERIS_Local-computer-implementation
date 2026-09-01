"""Read-only provenance verification for the locally reviewed PPTX capability."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import ROOT

PROVENANCE = ROOT / "config" / "pptx_beautify_lock.provenance.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def verify(_: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = json.loads(PROVENANCE.read_text(encoding="utf-8-sig"))
    checks = []
    source_root = ROOT / spec["source_root"]
    for rel, expected in spec["source_files"].items():
        path = source_root / rel
        actual = _sha256(path) if path.is_file() else None
        checks.append({"kind": "SOURCE", "path": str(path.relative_to(ROOT)), "expected_sha256": expected, "actual_sha256": actual, "valid": actual == expected})
    exe = ROOT / spec["executable"]["path"]
    actual = _sha256(exe) if exe.is_file() else None
    checks.append({"kind": "EXECUTABLE", "path": str(exe.relative_to(ROOT)), "expected_sha256": spec["executable"]["sha256"], "actual_sha256": actual, "bytes": exe.stat().st_size if exe.is_file() else None, "valid": actual == spec["executable"]["sha256"] and exe.stat().st_size == spec["executable"]["bytes"] if exe.is_file() else False})
    valid = all(item["valid"] for item in checks)
    return {"skill_id": "pptx-beautify-lock-local", "result": "PASS" if valid else "FAIL", "provenance_valid": valid, "checks": checks, "authenticode": spec["executable"]["authenticode"], "capability_maturity": spec["acceptance"], "production_acceptance": "NOT_RUN_NO_INPUT_PPTX", "truth": spec["truth"]}
