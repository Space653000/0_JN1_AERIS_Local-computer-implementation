"""Deterministic claim/evidence guard for AERIS model-generated role output.

A model response is never engineering Evidence by itself. This module forces role
responses through a small machine-readable schema before they can be rendered as an
engineering conclusion. Unsupported measured-fact claims are rejected rather than
shown as authoritative prose.
"""
from __future__ import annotations

import json
import re
from typing import Any

SCHEMA_VERSION = 1
ALLOWED_CLASSIFICATIONS = {"EVIDENCE", "INFERENCE", "HYPOTHESIS", "UNKNOWN"}

_MEASURED_FACT_PATTERNS = (
    re.compile(r"\b(measured|recorded|observed|verified|validated|calibrated)\b", re.I),
    re.compile(r"\b(test|measurement|calibration)\s+(passed|failed|shows?|showed|indicates?|indicated)\b", re.I),
    re.compile(r"測得|實測|量測(?:結果|記錄|資料|顯示)|記錄顯示|測試(?:已)?(?:通過|失敗)|校正(?:已)?完成|已有.{0,6}(?:量測|測試|校正)"),
)


def _extract_json(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].lstrip()
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("model output JSON must be an object")
        return value
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(raw):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(raw[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        raise ValueError("model output is not valid Evidence Schema JSON")


def _uses_measured_fact_wording(statement: str) -> bool:
    return any(pattern.search(statement) for pattern in _MEASURED_FACT_PATTERNS)


def validate_role_output(text: str, *, approved_evidence_refs: list[str] | None = None) -> dict[str, Any]:
    approved = {str(x).strip() for x in (approved_evidence_refs or []) if str(x).strip()}
    errors: list[str] = []
    try:
        payload = _extract_json(text)
    except ValueError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "accepted": False,
            "claim_authority": "REJECTED_NONCONFORMING_MODEL_OUTPUT",
            "claims": [],
            "missing_evidence": [],
            "recommended_tests": [],
            "errors": [str(exc)],
            "approved_evidence_refs": sorted(approved),
        }

    claims = payload.get("claims")
    if not isinstance(claims, list):
        errors.append("claims must be a list")
        claims = []

    normalized_claims: list[dict[str, Any]] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"claim[{index}] must be an object")
            continue
        statement = str(claim.get("statement", "")).strip()
        classification = str(claim.get("classification", "UNKNOWN")).upper().strip()
        refs = claim.get("evidence_refs", [])
        confidence = claim.get("confidence")
        if not statement:
            errors.append(f"claim[{index}] statement is required")
            continue
        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"claim[{index}] invalid classification: {classification}")
            continue
        if not isinstance(refs, list) or any(not isinstance(x, str) for x in refs):
            errors.append(f"claim[{index}] evidence_refs must be a list of strings")
            refs = []
        refs = [x.strip() for x in refs if x.strip()]
        unknown_refs = sorted(set(refs) - approved)
        if unknown_refs:
            errors.append(f"claim[{index}] references unapproved Evidence: {unknown_refs}")
        if classification == "EVIDENCE" and not refs:
            errors.append(f"claim[{index}] EVIDENCE classification requires approved evidence_refs")
        if classification == "EVIDENCE" and not approved:
            errors.append(f"claim[{index}] cannot be EVIDENCE because no authoritative Evidence was supplied")
        if classification != "EVIDENCE" and _uses_measured_fact_wording(statement):
            errors.append(f"claim[{index}] uses measured/verified-fact wording without EVIDENCE classification")
        if confidence is not None:
            try:
                number = float(confidence)
                if not 0.0 <= number <= 1.0:
                    errors.append(f"claim[{index}] confidence must be between 0 and 1")
            except (TypeError, ValueError):
                errors.append(f"claim[{index}] confidence must be numeric or null")
        normalized_claims.append(
            {
                "statement": statement,
                "classification": classification,
                "evidence_refs": refs,
                "confidence": confidence,
            }
        )

    missing = payload.get("missing_evidence", [])
    tests = payload.get("recommended_tests", payload.get("recommended_test", []))
    if isinstance(missing, str):
        missing = [missing]
    if isinstance(tests, str):
        tests = [tests]
    if not isinstance(missing, list):
        errors.append("missing_evidence must be a list or string")
        missing = []
    if not isinstance(tests, list):
        errors.append("recommended_tests must be a list or string")
        tests = []

    accepted = not errors
    has_evidence = any(c["classification"] == "EVIDENCE" for c in normalized_claims)
    if not accepted:
        authority = "REJECTED_UNSUPPORTED_OR_INVALID_CLAIM"
    elif has_evidence:
        authority = "SCHEMA_VALIDATED_WITH_EXPLICIT_EVIDENCE_REFS"
    else:
        authority = "SCHEMA_VALIDATED_INFERENCE_ONLY"
    return {
        "schema_version": SCHEMA_VERSION,
        "accepted": accepted,
        "claim_authority": authority,
        "claims": normalized_claims if accepted else [],
        "missing_evidence": [str(x).strip() for x in missing if str(x).strip()] if accepted else [],
        "recommended_tests": [str(x).strip() for x in tests if str(x).strip()] if accepted else [],
        "errors": errors,
        "approved_evidence_refs": sorted(approved),
    }


def render_guarded_output(guarded: dict[str, Any]) -> str:
    if not guarded.get("accepted"):
        detail = "; ".join(str(x) for x in guarded.get("errors", [])[:4])
        return (
            "【模型輸出已被 Evidence Guard 拒絕】\n"
            "此輸出不符合 AERIS 證據契約，因此不顯示為工程結論。"
            + (f"\n原因：{detail}" if detail else "")
        )
    lines = ["【AERIS Evidence-Guarded Role Output】", f"Authority: {guarded['claim_authority']}"]
    for claim in guarded.get("claims", []):
        refs = ", ".join(claim.get("evidence_refs", [])) or "none"
        lines.append(f"- [{claim['classification']}] {claim['statement']} (Evidence: {refs})")
    missing = guarded.get("missing_evidence", [])
    if missing:
        lines.append("Missing Evidence:")
        lines.extend(f"- {item}" for item in missing)
    tests = guarded.get("recommended_tests", [])
    if tests:
        lines.append("Recommended Tests:")
        lines.extend(f"- {item}" for item in tests)
    return "\n".join(lines)
