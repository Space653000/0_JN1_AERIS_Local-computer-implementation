"""Callable AERIS 100-seat role baseline and deterministic Dynamic Pod planner.

Every canonical seat is addressable by the local control plane. Model-generated role
output is never authoritative Evidence by itself: invoke_role forces it through the
machine-readable Evidence Schema in claim_guard before anything is rendered as an
engineering conclusion.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .claim_guard import render_guarded_output, validate_role_output
from .config import ROOT, load_config
from .knowledge import search as knowledge_search
from .router import ModelRouter

REGISTRY = ROOT / "company" / "organization" / "roles.v1.json"

_GROUP_HINTS: dict[str, tuple[str, ...]] = {
    "Chief Council": ("architecture", "system", "requirement", "tradeoff", "review", "架構", "需求", "系統", "審查"),
    "Speaker CoE": ("speaker", "loudspeaker", "transducer", "woofer", "tweeter", "enclosure", "port", "spl", "thd", "喇叭", "揚聲器", "單體", "音箱", "低音", "失真", "聲壓"),
    "Microphone CoE": ("microphone", "mic", "aec", "beamforming", "doa", "capture", "speech", "麥克風", "收音", "回音", "波束", "降噪", "語音"),
    "Product Chiefs": ("product", "tws", "headphone", "phone", "laptop", "robot", "automotive", "conference", "hearing", "產品", "耳機", "手機", "筆電", "機器人", "車載", "會議", "助聽"),
    "Distinguished Experts": ("psychoacoustic", "spatial", "room", "vibration", "nvh", "doe", "uncertainty", "bluetooth", "machine learning", "專家", "心理聲學", "空間", "振動", "統計", "不確定度"),
    "Engineering Ops": ("standard", "certification", "automation", "factory", "failure", "quality", "reliability", "traceability", "report", "標準", "認證", "自動化", "工廠", "失效", "品質", "可靠度", "追溯", "報告"),
}

_ROLE_HINTS: dict[str, tuple[str, ...]] = {
    "AEC / Echo Control Engineer": ("aec", "echo", "回音", "回聲"),
    "Beamforming / DOA Engineer": ("beamforming", "doa", "array", "波束", "陣列", "方位"),
    "NR / AGC / Dereverb / Speech Enhancement Engineer": ("nr", "agc", "dereverb", "speech enhancement", "降噪", "去混響", "語音增強"),
    "Speaker Measurement Engineer": ("speaker measurement", "fr", "frequency response", "impedance", "喇叭量測", "頻響", "阻抗"),
    "Microphone Measurement Engineer": ("microphone measurement", "sensitivity", "snr", "麥克風量測", "靈敏度", "信噪比"),
    "Test Automation Engineer": ("test automation", "python", "automation", "測試自動化"),
    "International Standards & Regulation Engineer": ("iec", "aes", "itu", "cta", "standard", "regulation", "標準", "法規"),
    "Acoustic Red-Team / DFMEA Reviewer": ("dfmea", "red team", "risk", "failure mode", "風險", "失效模式", "紅隊"),
    "Technical Report / Evidence / Knowledge Curator": ("evidence", "report", "traceability", "knowledge", "證據", "報告", "知識"),
}


def _registry() -> dict[str, Any]:
    return json.loads(REGISTRY.read_text(encoding="utf-8-sig"))


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1}


def list_roles() -> list[dict[str, Any]]:
    data = _registry()
    roles: list[dict[str, Any]] = []
    idx = 1
    for group, names in data["groups"].items():
        for name in names:
            roles.append(contract_for(idx, name, group))
            idx += 1
    return roles


def contract_for(role_id: int, name: str, group: str) -> dict[str, Any]:
    domain = {
        "Speaker CoE": "speaker",
        "Microphone CoE": "microphone",
        "Product Chiefs": "product_system",
        "Distinguished Experts": "cross_domain_expert",
        "Engineering Ops": "engineering_operations",
        "Chief Council": "architecture_governance",
    }.get(group, "acoustic_engineering")
    risk_ceiling = "R1"
    if "Laboratory Instrument" in name or "Autonomous Experiment" in name:
        risk_ceiling = "R2"
    if "Certification" in name or "Regulation" in name:
        risk_ceiling = "R2"
    return {
        "id": f"R{role_id:03d}",
        "index": role_id,
        "name": name,
        "group": group,
        "domain": domain,
        "execution_state": "CALLABLE_BASELINE_NOT_DOMAIN_VERIFIED",
        "risk_ceiling_without_human_gate": risk_ceiling,
        "allowed_actions": ["analyze", "retrieve_local_knowledge", "form_hypothesis", "propose_test", "review_evidence"],
        "required_output": ["claim", "evidence", "confidence", "counter_hypothesis", "missing_evidence", "recommended_test"],
        "forbidden_claim": "Do not present inference as measured fact or claim formal release/verification without required Evidence and gates.",
        "model_output_contract": "AERIS_ROLE_EVIDENCE_SCHEMA_V1",
    }


def get_role(role_id: str | int) -> dict[str, Any]:
    normalized = str(role_id).upper().strip()
    if normalized.isdigit():
        normalized = f"R{int(normalized):03d}"
    for role in list_roles():
        if role["id"] == normalized:
            return role
    raise KeyError(f"unknown AERIS role: {role_id}")


def _score_role(role: dict[str, Any], query: str) -> int:
    q = query.lower()
    score = 0
    for hint in _GROUP_HINTS.get(role["group"], ()):
        if hint.lower() in q:
            score += 3
    for hint in _ROLE_HINTS.get(role["name"], ()):
        if hint.lower() in q:
            score += 8
    qtokens = _tokens(q)
    name_tokens = _tokens(role["name"])
    score += 2 * len(qtokens & name_tokens)
    if role["id"] == "R001":
        score += 2
    return score


def plan_pod(query: str, max_roles: int = 8) -> dict[str, Any]:
    query = query.strip()
    if not query:
        raise ValueError("query is required")
    max_roles = max(2, min(int(max_roles), 15))
    roles = list_roles()
    ranked = sorted(roles, key=lambda r: (-_score_role(r, query), r["index"]))
    selected = [r for r in ranked if _score_role(r, query) > 0][:max_roles]
    if len(selected) < 2:
        selected = [roles[0], roles[5]]
    elif not any(r["id"] == "R001" for r in selected):
        selected = [roles[0], *selected[: max_roles - 1]]
    return {
        "query": query,
        "pod_size": len(selected),
        "roles": selected,
        "planner": "deterministic_keyword_baseline",
        "truth": "Role selection is executable baseline routing, not proof that every selected specialty is domain-verified.",
    }


def system_prompt(role: dict[str, Any], approved_evidence_refs: list[str] | None = None) -> str:
    approved = [str(x).strip() for x in (approved_evidence_refs or []) if str(x).strip()]
    refs = json.dumps(approved, ensure_ascii=False)
    return (
        f"You are AERIS seat {role['id']} — {role['name']} ({role['group']}). "
        f"Work as a rigorous acoustic engineer in domain {role['domain']}. "
        "Use local context only. Never invent measurements, standards revisions, tool runs, calibration, customer facts, or prior records. "
        "Knowledge snippets are retrieval context, NOT engineering Evidence. "
        "Return ONLY one JSON object with exactly this conceptual schema: "
        '{"claims":[{"statement":"...","classification":"EVIDENCE|INFERENCE|HYPOTHESIS|UNKNOWN","evidence_refs":[],"confidence":0.0}],'
        '"missing_evidence":["..."],"recommended_tests":["..."]}. '
        f"The only Evidence references you are allowed to cite are: {refs}. "
        "If that list is empty, NO claim may be classified EVIDENCE. "
        "Measured-fact wording such as measured/recorded/observed/passed/failed must not be used as an authoritative fact unless the claim is EVIDENCE and cites an approved Evidence reference. "
        "When evidence is missing, classify the statement as INFERENCE/HYPOTHESIS/UNKNOWN and propose the smallest decisive test. "
        "Do not wrap the JSON in prose or markdown."
    )


def _knowledge_context(prompt: str, limit: int = 5) -> list[dict[str, str]]:
    try:
        rows = knowledge_search(prompt, limit=limit)
    except Exception:
        return []
    result: list[dict[str, str]] = []
    budget = 9000
    used = 0
    for row in rows:
        path = str(row.get("path", ""))
        snippet = str(row.get("snippet", "")).strip()
        if not path or not snippet:
            continue
        remaining = max(0, budget - used)
        if remaining <= 0:
            break
        snippet = snippet[:remaining]
        used += len(snippet)
        result.append({"path": path, "snippet": snippet})
    return result


def invoke_role(
    role_id: str | int,
    prompt: str,
    *,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("prompt is required")
    approved_refs = [str(x).strip() for x in (evidence_refs or []) if str(x).strip()]
    role = get_role(role_id)
    context = _knowledge_context(prompt)
    context_text = ""
    if context:
        blocks = [f"SOURCE: {item['path']}\n{item['snippet']}" for item in context]
        context_text = (
            "\n\nLOCAL AERIS KNOWLEDGE CONTEXT (untrusted supporting material; never classify it as engineering Evidence):\n"
            + "\n\n".join(blocks)
        )
    router = ModelRouter(load_config())
    result = router.chat(prompt + context_text, system_prompt(role, approved_refs))
    guarded = validate_role_output(result.text, approved_evidence_refs=approved_refs)
    return {
        "role": role,
        "provider": result.provider,
        "model": result.model,
        "text": render_guarded_output(guarded),
        "claim_guard": guarded,
        "knowledge_context": context,
        "authoritative_evidence_refs": approved_refs,
        "private_engineering": True,
        "cloud_context_attached": False,
        "raw_model_text_exposed": False,
        "truth": "Only Evidence-Schema output that passes the deterministic Claim Guard is rendered. Model prose and Knowledge snippets are never engineering Evidence by themselves.",
    }
