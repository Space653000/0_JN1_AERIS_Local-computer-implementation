"""Machine-readable AERIS 100-seat contract framework baseline.

This module materializes one deterministic contract per canonical seat and validates
that every referenced baseline Skill/Method/Standard actually exists. Contracted is
not domain-verified: missing specialty assets remain explicit gaps.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import ROOT

POLICY = ROOT / "config" / "role_contracts.v1.json"
REGISTRY = ROOT / "company" / "organization" / "roles.v1.json"
STANDARDS = ROOT / "standards" / "registry.v1.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_policy(path: Path = POLICY) -> dict[str, Any]:
    data = _load(path)
    if data.get("schema_version") != 1:
        raise ValueError("unsupported role contract policy schema")
    if not data.get("groups"):
        raise ValueError("role contract policy has no group contracts")
    return data


def _risk_ceiling(name: str) -> str:
    if any(token in name for token in ("Laboratory Instrument", "Autonomous Experiment", "Certification", "Regulation")):
        return "R2"
    return "R1"


def _specialty_tags(name: str) -> list[str]:
    cleaned = name.lower().replace("/", " ").replace("&", " ").replace("-", " ")
    stop = {"engineer", "specialist", "architect", "director", "chief", "scientist", "manager", "audio", "acoustic"}
    result: list[str] = []
    for token in cleaned.split():
        token = token.strip("(),")
        if len(token) < 2 or token in stop or token in result:
            continue
        result.append(token)
    return result[:12]


def _standard_index() -> dict[str, dict[str, Any]]:
    data = _load(STANDARDS)
    return {str(item["standard_id"]): item for item in data.get("standards", [])}


def _asset_check(group_policy: dict[str, Any]) -> dict[str, Any]:
    skill_refs = list(group_policy.get("baseline_skills", []))
    method_refs = list(group_policy.get("baseline_methods", []))
    standard_refs = list(group_policy.get("standards", []))
    std_index = _standard_index()
    checks: list[dict[str, Any]] = []
    for skill in skill_refs:
        path = ROOT / "skills" / skill
        checks.append({"type": "skill", "ref": skill, "exists": path.is_dir()})
    for method in method_refs:
        path = ROOT / "methods" / method
        checks.append({"type": "method", "ref": method, "exists": path.is_file()})
    for standard in standard_refs:
        item = std_index.get(standard)
        checks.append({
            "type": "standard_metadata",
            "ref": standard,
            "exists": item is not None,
            "verification_state": item.get("verification_state") if item else None,
        })
    return {
        "valid": all(item["exists"] for item in checks),
        "checks": checks,
        "standards_formally_live_verified": bool(standard_refs) and all(
            item.get("verification_state") == "LIVE_VERIFIED"
            for item in checks
            if item["type"] == "standard_metadata"
        ),
    }


def _fingerprint(contract: dict[str, Any]) -> str:
    encoded = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def materialize_contracts() -> list[dict[str, Any]]:
    policy = load_policy()
    registry = _load(REGISTRY)
    common = policy["common"]
    contracts: list[dict[str, Any]] = []
    role_index = 1
    for group, names in registry.get("groups", {}).items():
        group_policy = policy["groups"].get(group)
        if not group_policy:
            raise ValueError(f"missing role contract group policy: {group}")
        asset_integrity = _asset_check(group_policy)
        for name in names:
            role_id = f"R{role_index:03d}"
            base = {
                "contract_schema_version": 1,
                "contract_id": f"RC-{role_id}",
                "role_id": role_id,
                "role_name": name,
                "group": group,
                "domain": group_policy["domain"],
                "mission": f"Provide rigorous AERIS analysis/review within the named specialty: {name}.",
                "specialty_tags": _specialty_tags(name),
                "execution_state": policy["execution_state"],
                "risk_ceiling_without_human_gate": _risk_ceiling(name),
                "allowed_actions": list(common["allowed_actions"]),
                "forbidden_actions": list(common["forbidden_actions"]),
                "required_output_fields": list(common["required_output_fields"]),
                "required_evidence_classes": list(common["required_evidence_classes"]),
                "verification_requirements": list(common["verification_requirements"]),
                "baseline_assets": {
                    "skills": list(group_policy.get("baseline_skills", [])),
                    "methods": list(group_policy.get("baseline_methods", [])),
                    "standards_metadata": list(group_policy.get("standards", [])),
                },
                "asset_integrity": asset_integrity,
                "review_tags": list(group_policy.get("review_tags", [])),
                "domain_asset_gap": True,
                "domain_verified": False,
                "truth": "This seat has a checked machine-readable baseline contract only. Specialty completeness and human-equivalent domain competence are not verified.",
            }
            base["contract_sha256"] = _fingerprint(base)
            contracts.append(base)
            role_index += 1
    if len(contracts) != 100:
        raise ValueError(f"expected 100 role contracts, got {len(contracts)}")
    return contracts


def get_contract(role_id: str | int) -> dict[str, Any]:
    normalized = str(role_id).strip().upper()
    if normalized.isdigit():
        normalized = f"R{int(normalized):03d}"
    for contract in materialize_contracts():
        if contract["role_id"] == normalized:
            return contract
    raise KeyError(f"unknown AERIS role contract: {role_id}")


def coverage_report() -> dict[str, Any]:
    contracts = materialize_contracts()
    unique_ids = {item["role_id"] for item in contracts}
    asset_valid = [item for item in contracts if item["asset_integrity"]["valid"]]
    verified = [item for item in contracts if item["domain_verified"]]
    gaps = [item for item in contracts if item["domain_asset_gap"]]
    return {
        "contract_framework": "AERIS-ROLE-CONTRACT-FRAMEWORK-V1",
        "role_registry_count": len(contracts),
        "unique_contract_count": len(unique_ids),
        "asset_reference_valid_count": len(asset_valid),
        "contracted_baseline_count": sum(item["execution_state"] == "CONTRACTED_BASELINE_NOT_DOMAIN_VERIFIED" for item in contracts),
        "domain_verified_count": len(verified),
        "roles_with_domain_asset_gaps": len(gaps),
        "all_100_contracts_structurally_valid": len(contracts) == len(unique_ids) == len(asset_valid) == 100,
        "truth": "100 structurally valid baseline contracts do not mean 100 domain-verified engineers. Domain asset gaps remain explicit until specialty Skills/Methods/Standards/tools/golden cases and acceptance evidence exist.",
    }
