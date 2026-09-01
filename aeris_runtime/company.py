"""Portable-company manifest validation for AERIS."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from .config import ROOT

MANIFEST = ROOT / "company" / "company.manifest.json"
MATURITY = ROOT / "config" / "maturity.json"
CORE_ALIGNMENT = ROOT / "config" / "core_alignment.json"
CORE_LOCK = ROOT / "core.lock.json"


@dataclass
class CompanyStatus:
    valid: bool
    company_id: str
    role_count: int
    modes: list[str]
    errors: list[str]


def load_company_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_company_manifest(path: Path = MANIFEST) -> CompanyStatus:
    errors = []
    try:
        data = load_company_manifest(path)
    except Exception as exc:
        return CompanyStatus(False, "UNKNOWN", 0, [], [f"manifest unreadable: {exc}"])

    company_id = str(data.get("company_id", ""))
    if company_id != "AERIS":
        errors.append("company_id must be AERIS")
    if data.get("product_stage") not in {"PRE_ALPHA", "ALPHA", "BETA", "RELEASE_CANDIDATE", "PRODUCTION"}:
        errors.append("product_stage must be explicit")

    org = data.get("organization", {})
    role_count = int(org.get("virtual_role_count", 0) or 0)
    if role_count != 100:
        errors.append("virtual_role_count must be 100")
    role_path = ROOT / org.get("role_registry", "company/organization/roles.v1.json")
    try:
        role_data = json.loads(role_path.read_text(encoding="utf-8-sig"))
        groups = role_data.get("groups", {})
        actual = sum(len(v) for v in groups.values())
        if actual != 100:
            errors.append(f"role registry must contain 100 roles, found {actual}")
        if role_data.get("maturity") != "DEFINED_NOT_ALL_EXECUTABLE":
            errors.append("role registry must truthfully expose current maturity")
    except Exception as exc:
        errors.append(f"role registry unreadable: {exc}")

    target = org.get("runtime_active_role_target", {})
    try:
        if [target["ordinary_task"]["min"], target["ordinary_task"]["max"]] != [2, 8]:
            errors.append("ordinary task pod target must preserve Core range 2-8")
        if [target["complex_task"]["min"], target["complex_task"]["max"]] != [5, 15]:
            errors.append("complex task pod target must preserve Core range 5-15")
        if not target.get("not_100_persistent_processes"):
            errors.append("100 seats must remain capabilities, not 100 persistent processes")
    except Exception:
        errors.append("runtime_active_role_target must explicitly encode ordinary 2-8 and complex 5-15")

    modes = list(data.get("runtime", {}).get("modes", []))
    if not {"offline", "local", "cloud", "auto"}.issubset(set(modes)):
        errors.append("runtime modes incomplete")
    if not str(data.get("core_target", {}).get("authority", "")).startswith("read_only"):
        errors.append("core target must be read_only")

    privacy = data.get("privacy", {})
    if not str(privacy.get("local_data_cloud_egress", "")).startswith("DENY"):
        errors.append("local data cloud egress must be DENY")

    try:
        maturity = json.loads(MATURITY.read_text(encoding="utf-8-sig"))
        if maturity.get("product_stage") != data.get("product_stage"):
            errors.append("maturity/product stage mismatch")
    except Exception as exc:
        errors.append(f"maturity matrix unreadable: {exc}")

    try:
        alignment = json.loads(CORE_ALIGNMENT.read_text(encoding="utf-8-sig"))
        lock = json.loads(CORE_LOCK.read_text(encoding="utf-8-sig"))
        reviewed_sha = str(alignment.get("canonical_core", {}).get("reviewed_sha", ""))
        if reviewed_sha != str(lock.get("baseline_sha", "")):
            errors.append("Core semantic alignment SHA does not match core.lock baseline")
        inv = alignment.get("non_negotiable_invariants", {})
        if inv.get("human_authority") != org.get("human_authority"):
            errors.append("Human authority drifted from Core alignment contract")
        if inv.get("virtual_seats") != role_count:
            errors.append("virtual seat count drifted from Core alignment contract")
    except Exception as exc:
        errors.append(f"Core alignment contract unreadable: {exc}")

    return CompanyStatus(not errors, company_id, role_count, modes, errors)
