"""Deterministic validation of the default zero-cost / no-Claude AERIS deployment profile.

This module validates repository policy and default entrypoints only. It does not make
legal conclusions about third-party software and it does not claim optional licensed
professional adapters are available.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import ROOT

POLICY_PATH = ROOT / "config" / "zero_cost_no_claude.v1.json"
AUTOPILOT_PATH = ROOT / "config" / "autopilot.json"
MATURITY_PATH = ROOT / "config" / "maturity.json"
DEFAULT_ENTRYPOINTS = (
    ROOT / "INSTALL_AERIS_LOCAL.ps1",
    ROOT / "AERIS_AUTOPILOT.ps1",
    ROOT / "scripts" / "one-click-install.ps1",
    ROOT / "scripts" / "autopilot.ps1",
    ROOT / "INSTALL_AERIS_LOCAL.sh",
    ROOT / "AERIS_AUTOPILOT.sh",
    ROOT / "scripts" / "one-click-install.sh",
    ROOT / "scripts" / "autopilot.sh",
)


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    data = _json(path)
    if data.get("schema_version") != 1:
        raise ValueError("unsupported zero-cost deployment policy schema")
    if data.get("profile_id") != "AERIS-ZERO-COST-NO-CLAUDE-V1":
        raise ValueError("unexpected zero-cost deployment profile")
    return data


def validate_default_deployment() -> dict[str, Any]:
    policy = load_policy()
    autopilot = _json(AUTOPILOT_PATH)
    maturity = _json(MATURITY_PATH)
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    monetary = policy.get("monetary_policy", {})
    ai = policy.get("ai_policy", {})
    defaults = autopilot.get("default_execution_policy", {})

    invariants = {
        "paid_software_not_required": monetary.get("paid_software_required") is False,
        "paid_cloud_api_not_required": monetary.get("paid_cloud_api_required") is False,
        "automatic_purchase_forbidden": monetary.get("automatic_purchase_allowed") is False,
        "auto_license_acceptance_forbidden": monetary.get("auto_accept_license_or_eula") is False,
        "claude_not_required": ai.get("claude_code_required") is False and ai.get("claude_token_required") is False,
        "autopilot_does_not_launch_claude": defaults.get("launch_claude_code") is False,
        "autopilot_does_not_launch_second_model": defaults.get("launch_second_model_reviewer") is False,
        "codex_is_primary_executor": defaults.get("primary_executor") == "codex",
        "default_model_matches": autopilot.get("default_local_model") == ai.get("default_local_model"),
    }
    for name, passed in invariants.items():
        checks.append({"check": name, "passed": bool(passed)})
        if not passed:
            errors.append(f"POLICY_INVARIANT_FAIL:{name}")

    forbidden = [str(x).lower() for x in policy.get("default_installer_forbidden_tokens", [])]
    for path in DEFAULT_ENTRYPOINTS:
        if not path.is_file():
            errors.append(f"DEFAULT_ENTRYPOINT_MISSING:{path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8-sig").lower()
        for token in forbidden:
            if token and token in text:
                errors.append(f"FORBIDDEN_DEFAULT_INSTALLER_TOKEN:{path.relative_to(ROOT)}:{token}")

    capabilities = maturity.get("capabilities", {})
    required_external_state = policy.get("required_state_for_paid_or_external_professional_capabilities")
    for capability in policy.get("paid_or_external_professional_capabilities", []):
        observed = capabilities.get(capability, {}).get("state")
        passed = observed == required_external_state
        checks.append({
            "check": f"external_capability:{capability}",
            "passed": passed,
            "observed": observed,
            "required": required_external_state,
        })
        if not passed:
            errors.append(f"PAID_OR_EXTERNAL_CAPABILITY_MUST_REMAIN_BLOCKED:{capability}:{observed}")

    return {
        "profile_id": policy["profile_id"],
        "valid": not errors,
        "errors": errors,
        "checks": checks,
        "claude_token_required": False,
        "paid_professional_software_required_for_default_opening": False,
        "truth": "VALID proves repository/default-entrypoint policy consistency only. It does not accept third-party licenses, prove future upstream pricing, or make optional licensed professional tools available.",
    }
