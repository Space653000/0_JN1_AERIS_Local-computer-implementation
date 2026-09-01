"""Machine-readable R0-R4 execution/approval policy for AERIS."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audit import append_event
from .config import ROOT

POLICY_FILE = ROOT / "config" / "risk_authority.json"


def load_policy(path: Path = POLICY_FILE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def decision(
    risk: str,
    *,
    automated_tests_passed: bool = False,
    preconditions_passed: bool = False,
    independent_review_passed: bool = False,
    human_approved: bool = False,
    human_authority: str = "",
    physical_or_hardware_risk: bool = False,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    policy = load_policy()
    risk = risk.strip().upper()
    level = policy.get("levels", {}).get(risk)
    if not level:
        raise ValueError(f"unsupported risk level: {risk}")
    refs = [str(x) for x in (evidence_refs or []) if str(x).strip()]
    blockers: list[str] = []

    if level.get("automated_tests_required") and not automated_tests_passed:
        blockers.append("AUTOMATED_TESTS_REQUIRED")
    if level.get("preconditions_required") and not preconditions_passed:
        blockers.append("PRECONDITIONS_REQUIRED")
    if level.get("independent_review_required") and not independent_review_passed:
        blockers.append("INDEPENDENT_REVIEW_REQUIRED")
    if level.get("human_confirmation_if_physical_or_hardware_risk") and physical_or_hardware_risk and not human_approved:
        blockers.append("HUMAN_CONFIRMATION_REQUIRED_FOR_PHYSICAL_OR_HARDWARE_RISK")
    if level.get("human_approval_required"):
        if not human_approved:
            blockers.append("HUMAN_APPROVAL_REQUIRED")
        if human_authority != str(level.get("human_authority", "Human Chief Engineer")):
            blockers.append("HUMAN_AUTHORITY_MISMATCH")
        if not refs:
            blockers.append("APPROVAL_EVIDENCE_REFERENCE_REQUIRED")

    automatic_allowed = bool(level.get("automatic_execution_allowed")) and not blockers
    if risk in {"R3", "R4"}:
        automatic_allowed = False
    return {
        "risk": risk,
        "policy_name": level.get("name"),
        "automatic_execution_allowed": automatic_allowed,
        "execution_allowed": not blockers,
        "blockers": blockers,
        "independent_review_required": bool(level.get("independent_review_required")),
        "human_approval_required": bool(level.get("human_approval_required")),
        "evidence_refs": refs,
        "truth": "R3/R4 are never self-authorized by AI even when prerequisites are otherwise satisfied",
    }


def record_decision(actor: str, risk: str, **kwargs: Any) -> dict[str, Any]:
    result = decision(risk, **kwargs)
    append_event("RISK_AUTHORITY_DECISION", actor, result)
    return result
