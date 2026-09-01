"""Versioned deterministic acoustic Golden regression baseline runner."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import ROOT
from . import skills_runtime

GOLDEN_ROOT = ROOT / "golden" / "acoustics" / "v1"
MANIFEST = GOLDEN_ROOT / "manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matches_expected(actual: Any, expected: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected object, got {type(actual).__name__}"]
        for key, expected_value in expected.items():
            if key not in actual:
                errors.append(f"{path}.{key}: missing")
                continue
            errors.extend(_matches_expected(actual[key], expected_value, f"{path}.{key}"))
        return errors
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected list, got {type(actual).__name__}"]
        if len(actual) != len(expected):
            errors.append(f"{path}: expected list length {len(expected)}, got {len(actual)}")
            return errors
        for index, expected_value in enumerate(expected):
            errors.extend(_matches_expected(actual[index], expected_value, f"{path}[{index}]"))
        return errors
    if actual != expected:
        errors.append(f"{path}: expected {expected!r}, got {actual!r}")
    return errors


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported Golden acoustic manifest schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Golden acoustic manifest contains no cases")
    ids = [str(item.get("case_id", "")) for item in cases]
    if any(not item for item in ids) or len(set(ids)) != len(ids):
        raise ValueError("Golden acoustic case_id values must be non-empty and unique")
    return payload


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    input_path = (GOLDEN_ROOT / str(case.get("input", ""))).resolve()
    try:
        input_path.relative_to(GOLDEN_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Golden acoustic input escapes suite root") from exc
    if not input_path.is_file() or input_path.is_symlink():
        raise ValueError(f"Golden acoustic input missing or invalid: {input_path.name}")
    actual_hash = _sha256(input_path)
    expected_hash = str(case.get("sha256", "")).lower()
    if not expected_hash or actual_hash != expected_hash:
        return {
            "case_id": case.get("case_id"),
            "result": "FAIL",
            "stage": "INPUT_INTEGRITY",
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "errors": ["golden input SHA-256 mismatch"],
        }

    params = dict(case.get("params") or {})
    params["input_path"] = str(input_path)
    original_roots = skills_runtime._ALLOWED_INPUT_ROOTS
    skills_runtime._ALLOWED_INPUT_ROOTS = tuple(original_roots) + (GOLDEN_ROOT,)
    try:
        actual = skills_runtime.run_skill(str(case.get("skill_id", "")), params)
    except Exception as exc:
        return {
            "case_id": case.get("case_id"),
            "result": "FAIL",
            "stage": "EXECUTION",
            "errors": [f"{type(exc).__name__}: {exc}"],
        }
    finally:
        skills_runtime._ALLOWED_INPUT_ROOTS = original_roots

    mismatches = _matches_expected(actual, case.get("expected", {}))
    return {
        "case_id": case.get("case_id"),
        "skill_id": case.get("skill_id"),
        "result": "PASS" if not mismatches else "FAIL",
        "stage": "EXPECTED_RESULT",
        "input_sha256": actual_hash,
        "errors": mismatches,
        "actual": actual,
    }


def run_suite(path: Path = MANIFEST) -> dict[str, Any]:
    manifest = load_manifest(path)
    results = [run_case(case) for case in manifest["cases"]]
    passed = sum(item["result"] == "PASS" for item in results)
    return {
        "suite_id": manifest.get("suite_id"),
        "result": "PASS" if passed == len(results) else "FAIL",
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
        "truth": manifest.get("truth"),
    }
