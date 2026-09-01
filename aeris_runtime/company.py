"""Portable-company manifest validation for AERIS."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import ROOT

MANIFEST = ROOT / "company" / "company.manifest.json"
MATURITY = ROOT / "config" / "maturity.json"
PROFILE_ROOT = ROOT / "config" / "machine_profiles"


@dataclass
class CompanyStatus:
    valid: bool
    company_id: str
    role_count: int
    modes: list[str]
    errors: list[str]


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_company_manifest(path: Path = MANIFEST) -> dict:
    return _json(path)


def validate_company_manifest(path: Path = MANIFEST) -> CompanyStatus:
    errors: list[str] = []
    try:
        data = load_company_manifest(path)
    except Exception as exc:
        return CompanyStatus(False, "UNKNOWN", 0, [], [f"manifest unreadable: {exc}"])

    try:
        schema_version = int(data.get("schema_version", 0))
    except (TypeError, ValueError):
        schema_version = 0
    if schema_version < 4:
        errors.append("company manifest schema_version must be >= 4")

    company_id = str(data.get("company_id", ""))
    if company_id != "AERIS":
        errors.append("company_id must be AERIS")
    if data.get("image_type") != "portable_company_image":
        errors.append("image_type must be portable_company_image")
    if data.get("product_stage") not in {"PRE_ALPHA", "ALPHA", "BETA", "RELEASE_CANDIDATE", "PRODUCTION"}:
        errors.append("product_stage must be explicit")

    core = data.get("core_target", {})
    if core.get("repository") != "Space653000/0_JN1_AERIS" or core.get("branch") != "main":
        errors.append("canonical Core repository/branch is incorrect")
    if not str(core.get("authority", "")).startswith("read_only"):
        errors.append("core target must be read_only")

    org = data.get("organization", {})
    role_count = int(org.get("virtual_role_count", 0) or 0)
    if role_count != 100:
        errors.append("virtual_role_count must be 100")
    if org.get("role_maturity") == "VERIFIED_100_ENGINEERS":
        errors.append("PRE_ALPHA must not claim VERIFIED_100_ENGINEERS")
    role_path = ROOT / org.get("role_registry", "company/organization/roles.v1.json")
    try:
        role_data = _json(role_path)
        groups = role_data.get("groups", {})
        actual = sum(len(v) for v in groups.values())
        if actual != 100:
            errors.append(f"role registry must contain 100 roles, found {actual}")
        if role_data.get("maturity") != "DEFINED_NOT_ALL_EXECUTABLE":
            errors.append("role registry must truthfully expose current maturity")
    except Exception as exc:
        errors.append(f"role registry unreadable: {exc}")

    modes = list(data.get("runtime", {}).get("modes", []))
    if not {"offline", "local", "cloud", "auto"}.issubset(set(modes)):
        errors.append("runtime modes incomplete")
    if data.get("runtime", {}).get("private_engineering") != "local_only_by_application_router":
        errors.append("private engineering must remain explicitly local-only at the application router")

    privacy = data.get("privacy", {})
    if not str(privacy.get("local_data_cloud_egress", "")).startswith("DENY"):
        errors.append("local data cloud egress must be DENY at the AERIS application boundary")
    if privacy.get("os_level_enforcement") != "REQUIRES_LOCAL_MACHINE_CONFIGURATION_AND_VERIFICATION":
        errors.append("OS-level privacy must not be claimed as repository-verified")

    profiles = data.get("deployment", {}).get("profiles", [])
    if not isinstance(profiles, list) or not profiles:
        errors.append("deployment profiles must be a non-empty list")
    else:
        for profile in profiles:
            if not (PROFILE_ROOT / f"{profile}.json").exists():
                errors.append(f"declared machine profile missing: {profile}")

    truth_rules = set(data.get("truth_rules", []))
    required_truth = {
        "core_overrides_implementation_when_conflicting",
        "defined_role_is_not_verified_engineer",
        "supported_machine_profile_is_not_verified_machine",
        "installed_is_not_verified",
        "tested_is_not_verified",
        "ci_kernel_pass_is_not_company_complete",
    }
    missing_truth = sorted(required_truth - truth_rules)
    if missing_truth:
        errors.append(f"required anti-fantasy truth rules missing: {missing_truth}")

    try:
        maturity = _json(MATURITY)
        if maturity.get("product_stage") != data.get("product_stage"):
            errors.append("maturity/product stage mismatch")
        allowed = set(maturity.get("states", []))
        if not {"NOT_IMPLEMENTED", "IMPLEMENTED", "TESTED", "VERIFIED", "BLOCKED_EXTERNAL"}.issubset(allowed):
            errors.append("maturity state vocabulary is incomplete")
    except Exception as exc:
        errors.append(f"maturity matrix unreadable: {exc}")

    return CompanyStatus(not errors, company_id, role_count, modes, errors)
