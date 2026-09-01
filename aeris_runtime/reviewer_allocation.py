"""Deterministic task-aware independent-reviewer allocation baseline for AERIS.

Allocation separates primary execution from review identity/context/permissions and
uses task/domain hints to rank reviewer capability seats. It selects seats only; it
does not launch Claude or any external model by default, and allocation is not proof
that a review occurred.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from .authority import load_policy as load_risk_policy
from .role_contracts import get_contract, load_policy as load_role_policy

_REVIEW_HINTS: dict[str, tuple[str, ...]] = {
    "standards": ("standard", "regulation", "certification", "iec", "aes", "itu", "cta", "標準", "法規", "認證"),
    "test_automation": ("automation", "script", "python", "reproduce", "regression", "自動化", "腳本", "重現", "回歸"),
    "reliability": ("reliability", "halt", "thermal", "environment", "lifetime", "可靠度", "壽命", "熱", "環境"),
    "requirements": ("requirement", "spec", "traceability", "configuration", "需求", "規格", "追溯", "配置"),
    "red_team": ("risk", "failure", "dfmea", "safety", "regression", "風險", "失效", "安全", "紅隊"),
    "evidence": ("evidence", "report", "provenance", "audit", "record", "證據", "報告", "來源", "稽核", "紀錄"),
    "quality": ("measurement", "validation", "quality", "pass", "fail", "speaker", "microphone", "量測", "驗證", "品質", "喇叭", "麥克風"),
}

_GROUP_BIAS: dict[str, tuple[str, ...]] = {
    "Chief Council": ("requirements", "red_team", "evidence", "quality"),
    "Speaker CoE": ("quality", "red_team", "evidence", "requirements"),
    "Microphone CoE": ("quality", "red_team", "evidence", "requirements"),
    "Product Chiefs": ("requirements", "quality", "red_team", "evidence"),
    "Distinguished Experts": ("red_team", "evidence", "quality", "requirements"),
    "Engineering Ops": ("red_team", "evidence", "quality", "requirements"),
}


def _normalize_task(task_context: str, task_tags: list[str] | None) -> str:
    parts = [str(task_context or "").strip()]
    parts.extend(str(item).strip() for item in (task_tags or []) if str(item).strip())
    return " ".join(parts).strip().lower()


def _score_candidate(key: str, task_text: str, primary_group: str, index: int) -> tuple[int, int]:
    score = 0
    for hint in _REVIEW_HINTS.get(key, ()):
        if hint.lower() in task_text:
            score += 10
    bias = _GROUP_BIAS.get(primary_group, ())
    if key in bias:
        score += max(1, 5 - bias.index(key))
    if key == "red_team":
        score += 2
    return score, -index


def allocate_reviewers(
    primary_role_id: str | int,
    risk: str,
    *,
    task_context: str = "",
    task_tags: list[str] | None = None,
) -> dict[str, Any]:
    primary = get_contract(primary_role_id)
    risk = str(risk).strip().upper()
    risk_policy = load_risk_policy().get("levels", {}).get(risk)
    if not risk_policy:
        raise ValueError(f"unsupported risk level: {risk}")

    independent_required = bool(risk_policy.get("independent_review_required"))
    human_required = bool(risk_policy.get("human_approval_required"))
    human_confirmation_if_physical = bool(risk_policy.get("human_confirmation_if_physical_or_hardware_risk"))
    reviewer_ids = load_role_policy()["reviewer_roles"]
    task_text = _normalize_task(task_context, task_tags)

    if not independent_required:
        selected: list[dict[str, Any]] = []
        ranked_keys: list[str] = []
    else:
        candidates: list[tuple[str, dict[str, Any], int]] = []
        for index, (key, role_id) in enumerate(reviewer_ids.items()):
            if role_id == primary["role_id"]:
                continue
            candidate = get_contract(role_id)
            candidates.append((key, candidate, index))
        candidates.sort(
            key=lambda item: (
                -_score_candidate(item[0], task_text, primary["group"], item[2])[0],
                item[2],
                item[1]["role_id"],
            )
        )
        required_count = 2 if risk in {"R3", "R4"} else 1
        selected = []
        ranked_keys = []
        for key, candidate, _index in candidates:
            selected.append({
                "role_id": candidate["role_id"],
                "role_name": candidate["role_name"],
                "group": candidate["group"],
                "review_specialty": key,
                "review_tags": candidate["review_tags"],
                "context_policy": "FRESH_REVIEW_CONTEXT_REQUIRED",
                "permissions": ["read_task", "read_evidence", "read_methods", "record_review"],
                "forbidden_permissions": ["repair_same_change", "approve_own_change", "write_primary_evidence", "human_release_approval"],
            })
            ranked_keys.append(key)
            if len(selected) == required_count:
                break
        if len(selected) != required_count:
            raise RuntimeError("insufficient independent reviewer seats")

    task_fingerprint = hashlib.sha256(task_text.encode("utf-8")).hexdigest() if task_text else None
    return {
        "primary_role_id": primary["role_id"],
        "primary_role_name": primary["role_name"],
        "primary_group": primary["group"],
        "risk": risk,
        "task_context_provided": bool(task_text),
        "task_context_sha256": task_fingerprint,
        "allocation_basis": "task_hint_score_plus_primary_group_bias" if task_text else "primary_group_bias_fallback",
        "selected_review_specialties": ranked_keys,
        "independent_review_required": independent_required,
        "reviewers": selected,
        "reviewer_count": len(selected),
        "same_identity_review_forbidden": True,
        "same_context_repair_and_approval_forbidden": True,
        "launch_external_model_by_default": False,
        "claude_required": False,
        "human_approval_required": human_required,
        "human_authority": "Human Chief Engineer" if human_required else None,
        "human_confirmation_if_physical_or_hardware_risk": human_confirmation_if_physical,
        "truth": "This is deterministic task-aware reviewer-seat allocation and separation policy. It does not prove a review occurred; completion still requires an actual review record/Evidence and Human authority where risk policy requires it.",
    }
