"""AERIS deterministic reproduction baseline for Skill-based Evidence Bundles."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from .config import ROOT
from .evidence import bundle_dir, validate_bundle
from .skills_runtime import run_skill

REPRO_ROOT = ROOT / ".aeris" / "reproduction"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def reproduce_run(run_id: str) -> dict[str, Any]:
    integrity = validate_bundle(run_id)
    if not integrity.get("valid"):
        return {"result": "FAIL", "run_id": run_id, "reason": "EVIDENCE_INTEGRITY_FAILED", "integrity": integrity}
    root = bundle_dir(run_id)
    method = json.loads((root / "method_snapshot.json").read_text(encoding="utf-8-sig"))
    expected = json.loads((root / "processed" / "skill_result.json").read_text(encoding="utf-8-sig"))
    input_manifest = json.loads((root / "input_manifest.json").read_text(encoding="utf-8-sig"))
    skill_id = method.get("skill_id")
    if not skill_id:
        return {"result": "BLOCKED", "run_id": run_id, "reason": "NO_DETERMINISTIC_SKILL_ID"}
    inputs = input_manifest.get("inputs", [])
    if len(inputs) != 1:
        return {"result": "BLOCKED", "run_id": run_id, "reason": "BASELINE_SUPPORTS_EXACTLY_ONE_FILE_INPUT"}
    source = root / str(inputs[0]["stored"])
    if not source.is_file() or _sha256(source) != str(inputs[0].get("sha256")):
        return {"result": "FAIL", "run_id": run_id, "reason": "RAW_INPUT_HASH_MISMATCH"}

    target_dir = REPRO_ROOT / run_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    shutil.copy2(source, target)
    params = dict(method.get("parameters") or {})
    params["input_path"] = str(target)
    requirement_path = root / "requirement_snapshot.json"
    requirement = json.loads(requirement_path.read_text(encoding="utf-8-sig"))
    if requirement:
        params["requirement"] = requirement

    import aeris_runtime.skills_runtime as skills_runtime
    original = skills_runtime._ALLOWED_INPUT_ROOTS
    try:
        skills_runtime._ALLOWED_INPUT_ROOTS = (*original, REPRO_ROOT)
        actual = run_skill(str(skill_id), params)
    finally:
        skills_runtime._ALLOWED_INPUT_ROOTS = original

    matches = actual == expected
    report = {
        "schema_version": 1,
        "run_id": run_id,
        "result": "PASS" if matches else "FAIL",
        "skill_id": skill_id,
        "expected": expected,
        "actual": actual,
        "exact_result_match": matches,
        "scope": "deterministic Skill replay only; external tools/hardware/environment reproduction requires their own adapters and locks",
    }
    (target_dir / "REPRODUCTION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
