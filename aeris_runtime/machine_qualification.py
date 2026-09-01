"""Deterministic AERIS machine qualification baseline.

This module evaluates already-detected machine facts against a versioned contract.
It never upgrades CI or inventory facts into real-machine VERIFIED claims.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import ROOT

CONTRACT_PATH = ROOT / "config" / "machine_qualification.v1.json"


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported machine qualification schema")
    if not isinstance(payload.get("workloads"), dict) or not payload["workloads"]:
        raise ValueError("machine qualification contract has no workloads")
    return payload


def _version_tuple(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    parts: list[int] = []
    for raw in str(value).split("."):
        digits = "".join(ch for ch in raw if ch.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts) if parts else None


def _numeric_check(name: str, actual: Any, minimum: float) -> dict[str, Any]:
    if actual is None:
        return {"name": name, "result": "UNKNOWN", "actual": None, "minimum": minimum}
    try:
        value = float(actual)
    except (TypeError, ValueError):
        return {"name": name, "result": "UNKNOWN", "actual": actual, "minimum": minimum}
    return {
        "name": name,
        "result": "PASS" if value >= minimum else "FAIL",
        "actual": value,
        "minimum": minimum,
    }


def qualify_facts(facts: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    profile = str(facts.get("profile", "unsupported-unprofiled"))
    tools = facts.get("tools", {}) if isinstance(facts.get("tools"), dict) else {}
    python_version = _version_tuple(str(facts.get("python_version", "")))
    gpu_text = str(facts.get("gpu", "")).lower()

    workload_results: dict[str, Any] = {}
    for workload_id, rule in contract["workloads"].items():
        applies = rule.get("applies_to_profiles", ["*"])
        if "*" not in applies and profile not in applies:
            workload_results[workload_id] = {
                "state": "NOT_APPLICABLE",
                "checks": [],
            }
            continue

        checks: list[dict[str, Any]] = []
        if "min_ram_gb" in rule:
            checks.append(_numeric_check("ram_gb", facts.get("ram_gb"), float(rule["min_ram_gb"])))
        if "min_disk_free_gb" in rule:
            checks.append(_numeric_check("disk_free_gb", facts.get("disk_free_gb"), float(rule["min_disk_free_gb"])))
        if "python_min" in rule:
            required = _version_tuple(str(rule["python_min"])) or ()
            if python_version is None:
                checks.append({"name": "python_version", "result": "UNKNOWN", "actual": None, "minimum": rule["python_min"]})
            else:
                checks.append({
                    "name": "python_version",
                    "result": "PASS" if python_version >= required else "FAIL",
                    "actual": ".".join(map(str, python_version)),
                    "minimum": rule["python_min"],
                })
        for tool in rule.get("required_tools", []):
            present = tools.get(tool)
            checks.append({
                "name": f"tool:{tool}",
                "result": "PASS" if present is True else ("FAIL" if present is False else "UNKNOWN"),
                "actual": present,
                "required": True,
            })
        vendor = str(rule.get("required_gpu_vendor", "")).strip().lower()
        if vendor:
            if not gpu_text or gpu_text == "not_detected":
                result = "FAIL"
            else:
                result = "PASS" if vendor in gpu_text else "FAIL"
            checks.append({"name": "gpu_vendor", "result": result, "actual": facts.get("gpu"), "required": vendor})
        if "min_vram_gb" in rule:
            checks.append(_numeric_check("vram_gb", facts.get("vram_gb"), float(rule["min_vram_gb"])))

        results = {item["result"] for item in checks}
        if "FAIL" in results:
            state = "NOT_QUALIFIED"
        elif "UNKNOWN" in results:
            state = "BLOCKED_INCOMPLETE_EVIDENCE"
        else:
            state = "QUALIFIED_BASELINE"
        workload_results[workload_id] = {"state": state, "checks": checks}

    baseline_required = list(contract.get("baseline_required_workloads", []))
    baseline_states = [workload_results.get(item, {}).get("state") for item in baseline_required]
    baseline_pass = bool(baseline_required) and all(state == "QUALIFIED_BASELINE" for state in baseline_states)
    if profile == "unsupported-unprofiled":
        overall = "UNSUPPORTED_PROFILE"
    elif baseline_pass:
        overall = "QUALIFIED_BASELINE"
    elif any(state == "NOT_QUALIFIED" for state in baseline_states):
        overall = "NOT_QUALIFIED"
    else:
        overall = "BLOCKED_INCOMPLETE_EVIDENCE"

    return {
        "contract_id": contract.get("contract_id"),
        "profile": profile,
        "overall_state": overall,
        "baseline_required_workloads": baseline_required,
        "workloads": workload_results,
        "truth": "QUALIFIED_BASELINE covers deterministic inventory checks only; it is not real-machine VERIFIED evidence and does not cover sustained load, latency, thermal, reboot, hard-offline, licenses, instruments or calibration.",
    }
