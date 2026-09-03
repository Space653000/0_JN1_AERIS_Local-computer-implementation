"""Deterministic local acoustic Skills baseline.

These Skills operate on local CSV/JSON inputs and produce machine-readable results.
They are intentionally calculation/validation primitives rather than LLM guesses.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from .config import ROOT

SKILLS_ROOT = ROOT / "skills"
_ALLOWED_INPUT_ROOTS = (ROOT / "data", ROOT / ".aeris" / "imports")


def list_skills() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not SKILLS_ROOT.exists():
        return result
    for manifest in sorted(SKILLS_ROOT.glob("*/manifest.json")):
        try:
            item = json.loads(manifest.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        item["manifest_path"] = str(manifest.relative_to(ROOT))
        result.append(item)
    return result


def _resolve_input(value: str) -> Path:
    raw = Path(value)
    path = raw if raw.is_absolute() else ROOT / raw
    path = path.resolve()
    allowed = False
    for root in _ALLOWED_INPUT_ROOTS:
        try:
            path.relative_to(root.resolve())
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        raise ValueError("Skill input must be under data/ or .aeris/imports/")
    if not path.is_file() or path.is_symlink():
        raise ValueError("Skill input file not found or is a symlink")
    return path


def _pick(fieldnames: list[str], options: tuple[str, ...]) -> str:
    normalized = {name.strip().lower(): name for name in fieldnames}
    for option in options:
        if option in normalized:
            return normalized[option]
    raise ValueError(f"CSV missing required column; expected one of {options}")


def load_frequency_response_csv(value: str) -> dict[str, Any]:
    path = _resolve_input(value)
    points: list[tuple[float, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        fcol = _pick(reader.fieldnames, ("frequency_hz", "frequency", "freq_hz", "freq"))
        lcol = _pick(reader.fieldnames, ("level_db", "spl_db", "magnitude_db", "db"))
        for row_no, row in enumerate(reader, 2):
            try:
                freq = float(str(row.get(fcol, "")).strip())
                level = float(str(row.get(lcol, "")).strip())
            except ValueError as exc:
                raise ValueError(f"non-numeric FR value at CSV row {row_no}") from exc
            if not math.isfinite(freq) or not math.isfinite(level):
                raise ValueError(f"non-finite FR value at CSV row {row_no}")
            if freq <= 0:
                raise ValueError(f"frequency must be >0 at CSV row {row_no}")
            points.append((freq, level))
    if len(points) < 2:
        raise ValueError("frequency-response CSV requires at least two points")
    return {"path": str(path), "points": points}


def measurement_import_validation(input_path: str) -> dict[str, Any]:
    data = load_frequency_response_csv(input_path)
    points = data["points"]
    freqs = [p[0] for p in points]
    duplicate_count = len(freqs) - len(set(freqs))
    strictly_increasing = all(b > a for a, b in zip(freqs, freqs[1:]))
    issues: list[str] = []
    if duplicate_count:
        issues.append(f"DUPLICATE_FREQUENCIES:{duplicate_count}")
    if not strictly_increasing:
        issues.append("FREQUENCY_NOT_STRICTLY_INCREASING")
    return {
        "skill_id": "measurement-import-validation",
        "result": "PASS" if not issues else "FAIL",
        "input": data["path"],
        "points": len(points),
        "frequency_min_hz": min(freqs),
        "frequency_max_hz": max(freqs),
        "duplicate_frequency_count": duplicate_count,
        "strictly_increasing": strictly_increasing,
        "issues": issues,
        "evidence_class": "DETERMINISTIC_FILE_VALIDATION",
    }


def frequency_response_analysis(input_path: str, low_hz: float = 20.0, high_hz: float = 20000.0) -> dict[str, Any]:
    if low_hz <= 0 or high_hz <= low_hz:
        raise ValueError("invalid analysis band")
    data = load_frequency_response_csv(input_path)
    selected = [(f, level) for f, level in data["points"] if low_hz <= f <= high_hz]
    if len(selected) < 2:
        raise ValueError("analysis band contains fewer than two points")
    levels = [p[1] for p in selected]
    avg = sum(levels) / len(levels)
    minimum = min(levels)
    maximum = max(levels)
    rms_dev = math.sqrt(sum((x - avg) ** 2 for x in levels) / len(levels))
    min_point = min(selected, key=lambda p: p[1])
    max_point = max(selected, key=lambda p: p[1])
    return {
        "skill_id": "frequency-response-analysis",
        "result": "PASS",
        "input": data["path"],
        "band_hz": [low_hz, high_hz],
        "points": len(selected),
        "average_db": round(avg, 6),
        "minimum_db": round(minimum, 6),
        "maximum_db": round(maximum, 6),
        "peak_to_peak_db": round(maximum - minimum, 6),
        "rms_deviation_db": round(rms_dev, 6),
        "minimum_point": {"frequency_hz": min_point[0], "level_db": min_point[1]},
        "maximum_point": {"frequency_hz": max_point[0], "level_db": max_point[1]},
        "evidence_class": "DETERMINISTIC_NUMERICAL_ANALYSIS",
    }


def requirement_verification(input_path: str, requirement: dict[str, Any]) -> dict[str, Any]:
    band = requirement.get("band_hz", [20.0, 20000.0])
    if not isinstance(band, list) or len(band) != 2:
        raise ValueError("requirement.band_hz must contain [low, high]")
    analysis = frequency_response_analysis(input_path, float(band[0]), float(band[1]))
    checks: list[dict[str, Any]] = []

    def check(name: str, actual: float, op: str, limit: float) -> None:
        passed = actual <= limit if op == "<=" else actual >= limit
        margin = (limit - actual) if op == "<=" else (actual - limit)
        checks.append({"name": name, "actual": actual, "operator": op, "limit": limit, "margin": round(margin, 6), "result": "PASS" if passed else "FAIL"})

    if "max_peak_to_peak_db" in requirement:
        check("max_peak_to_peak_db", float(analysis["peak_to_peak_db"]), "<=", float(requirement["max_peak_to_peak_db"]))
    if "max_rms_deviation_db" in requirement:
        check("max_rms_deviation_db", float(analysis["rms_deviation_db"]), "<=", float(requirement["max_rms_deviation_db"]))
    if "minimum_average_db" in requirement:
        check("minimum_average_db", float(analysis["average_db"]), ">=", float(requirement["minimum_average_db"]))
    if "maximum_average_db" in requirement:
        check("maximum_average_db", float(analysis["average_db"]), "<=", float(requirement["maximum_average_db"]))
    if not checks:
        raise ValueError("requirement contains no supported checks")
    overall = "PASS" if all(c["result"] == "PASS" for c in checks) else "FAIL"
    return {
        "skill_id": "requirement-verification",
        "result": overall,
        "input": analysis["input"],
        "band_hz": analysis["band_hz"],
        "checks": checks,
        "analysis": analysis,
        "evidence_class": "DETERMINISTIC_REQUIREMENT_CHECK",
    }


def run_skill(skill_id: str, params: dict[str, Any]) -> dict[str, Any]:
    manifest_path=SKILLS_ROOT / skill_id / "manifest.json"
    if manifest_path.resolve().is_relative_to(SKILLS_ROOT.resolve()) and manifest_path.is_file():
        manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if manifest.get("domain_factory_contract") is True:
            from .engineering.domain_methods import execute
            return execute(skill_id,params)
        if manifest.get("factory_contract") is True:
            from .engineering.catalog import execute
            return execute(skill_id,params)
    if skill_id == "free-local-acoustic-baseline":
        from .free_acoustics import analyze
        return analyze(params)
    if skill_id == "pptx-beautify-lock-local":
        from .pptx_provenance import verify
        return verify(params)
    if skill_id == "measurement-import-validation":
        return measurement_import_validation(str(params.get("input_path", "")))
    if skill_id == "frequency-response-analysis":
        return frequency_response_analysis(str(params.get("input_path", "")), float(params.get("low_hz", 20.0)), float(params.get("high_hz", 20000.0)))
    if skill_id == "requirement-verification":
        requirement = params.get("requirement")
        if not isinstance(requirement, dict):
            raise ValueError("requirement must be an object")
        return requirement_verification(str(params.get("input_path", "")), requirement)
    raise KeyError(f"unknown skill: {skill_id}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="aeris-skills")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    run = sub.add_parser("run")
    run.add_argument("skill_id")
    run.add_argument("--params-json", required=True)
    args = parser.parse_args()
    try:
        if args.command == "list":
            payload: Any = {"skills": list_skills()}
        else:
            payload = run_skill(args.skill_id, json.loads(args.params_json))
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "detail": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
