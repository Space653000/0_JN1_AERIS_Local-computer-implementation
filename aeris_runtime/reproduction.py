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


def _canonical_result(value: Any) -> Any:
    """Remove transport-only input paths while preserving engineering result values."""
    if isinstance(value, dict):
        return {key: ("<INPUT>" if key in {"input", "input_path", "path"} else _canonical_result(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonical_result(item) for item in value]
    return value


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
    if expected.get("capability_maturity") == "FREE_LOCAL_BASELINE":
        from .engineering.catalog import digest
        raw=root/"raw"/"engineering-input.json"
        if not raw.is_file():
            return {"result":"FAIL","run_id":run_id,"reason":"MISSING_SEALED_ENGINEERING_INPUT"}
        params=json.loads(raw.read_text(encoding="utf-8"))
        if digest(params)!=expected.get("input_sha256"):
            return {"result":"FAIL","run_id":run_id,"reason":"ENGINEERING_INPUT_HASH_MISMATCH"}
        actual=run_skill(str(skill_id),params)
        matches=actual==expected
        report={"schema_version":3,"run_id":run_id,"skill_id":skill_id,"result":"PASS" if matches else "FAIL",
                "deterministic_result_match":matches,"expected_sha256":digest(expected),"actual_sha256":digest(actual),
                "scope":"sealed inline-JSON engineering input replay with exact implementation and output hashes"}
        target_dir=REPRO_ROOT/run_id; target_dir.mkdir(parents=True,exist_ok=True)
        (target_dir/"REPRODUCTION_REPORT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        return report
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

    expected_canonical = _canonical_result(expected)
    actual_canonical = _canonical_result(actual)
    matches = actual_canonical == expected_canonical
    report = {
        "schema_version": 2,
        "run_id": run_id,
        "result": "PASS" if matches else "FAIL",
        "skill_id": skill_id,
        "expected": expected,
        "actual": actual,
        "canonical_expected": expected_canonical,
        "canonical_actual": actual_canonical,
        "deterministic_result_match": matches,
        "path_fields_normalized": ["input", "input_path", "path"],
        "scope": "deterministic Skill replay; transport-only file paths are normalized. External tools/hardware/environment reproduction require their own adapters and locks.",
    }
    (target_dir / "REPRODUCTION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
