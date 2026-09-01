"""Deterministic independent-reviewer allocation baseline for AERIS.

Allocation separates primary execution from review identity/context/permissions. It
selects capability seats; it does not launch Claude or any model by default.
"""
from __future__ import annotations

from typing import Any

from .authority import load_policy as load_risk_policy
from .role_contracts import get_contract, load_policy as load_role_policy


def allocate_reviewers(primary_role_id: str | int, risk: str) -> dict[str, Any]:
    primary = get_contract(primary_role_id)
    risk = str(risk).strip().upper()
    risk_policy = load_risk_policy().get("levels", {}).get(risk)
    if not risk_policy:
        raise ValueError(f"unsupported risk level: {risk}")

    independent_required = bool(risk_policy.get("independent_review_required"))
    human_required = bool(risk_policy.get("human_approval_required"))
    human_confirmation_if_physical = bool(risk_policy.get("human_confirmation_if_physical_or_hardware_risk"))
    reviewer_ids = load_role_policy()["reviewer_roles"]

    if not independent_required:
        selected: list[dict[str, Any]] = []
    else:
        priority = [
            reviewer_ids["red_team"],
            reviewer_ids["evidence"],
            reviewer_ids["quality"],
            reviewer_ids["requirements"],
        ]
        required_count = 2 if risk in {"R3", "R4"} else 1
        selected = []
        for role_id in priority:
            if role_id == primary["role_id"]:
                continue
            candidate = get_contract(role_id)
            selected.append({
                "role_id": candidate["role_id"],
                "role_name": candidate["role_name"],
                "group": candidate["group"],
                "review_tags": candidate["review_tags"],
                "context_policy": "FRESH_REVIEW_CONTEXT_REQUIRED",
                "permissions": ["read_task", "read_evidence", "read_methods", "record_review"],
                "forbidden_permissions": ["repair_same_change", "approve_own_change", "write_primary_evidence", "human_release_approval"],
            })
            if len(selected) == required_count:
                break
        if len(selected) != required_count:
            raise RuntimeError("insufficient independent reviewer seats")

    return {
        "primary_role_id": primary["role_id"],
        "primary_role_name": primary["role_name"],
        "risk": risk,
        "independent_review_required": independent_required,
        "reviewers": selected,
        "reviewer_count": len(selected),
        "same_identity_review_forbidden": True,
        "same_context_repair_and_approval_forbidden": True,
        "launch_external_model_by_default": False,
        "human_approval_required": human_required,
        "human_authority": "Human Chief Engineer" if human_required else None,
        "human_confirmation_if_physical_or_hardware_risk": human_confirmation_if_physical,
        "truth": "This is deterministic reviewer-seat allocation and separation policy. It does not prove a review occurred; completion still requires an actual review record/Evidence and Human authority where risk policy requires it.",
    }
