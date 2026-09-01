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
AUTOPILOT = ROOT / "config" / "autopilot.json"
RISK_AUTHORITY = ROOT / "config" / "risk_authority.json"


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
    errors: list[str] = []
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

    operating = data.get("human_ai_operating_model", {})
    if operating.get("human_chief_engineer") != "final_authority":
        errors.append("Human Chief Engineer final authority missing")
    if operating.get("codex") != "primary_local_executor_installer_implementer":
        errors.append("Codex executor role drifted")
    if operating.get("claude_code") != "independent_reviewer_acceptance_auditor":
        errors.append("Claude reviewer role drifted")
    if operating.get("same_context_repair_and_independent_approval_allowed") is not False:
        errors.append("same-context repair and independent approval must be false")

    auto = data.get("autopilot", {})
    required_entrypoints = [
        auto.get("windows_entrypoint"), auto.get("linux_jetson_entrypoint"),
        auto.get("claude_windows_entrypoint"), auto.get("claude_linux_jetson_entrypoint"),
    ]
    for entry in required_entrypoints:
        if not entry or not (ROOT / str(entry)).is_file():
            errors.append(f"Autopilot/reviewer entrypoint missing: {entry}")
    if auto.get("installation_equals_opening") is not False or auto.get("ci_smoke_equals_real_acceptance") is not False:
        errors.append("Autopilot truth boundary weakened")

    operations = data.get("operations", {})
    if operations.get("public_supervisor_bind") is not False:
        errors.append("local supervisor public bind must remain forbidden")
    if operations.get("verified_scope_requires_real_machine_acceptance") is not True:
        errors.append("OPEN_VERIFIED_SCOPE must require real-machine acceptance")

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
        if str(data.get("core_target", {}).get("reviewed_sha", "")) != reviewed_sha:
            errors.append("company manifest Core reviewed SHA does not match alignment")
        inv = alignment.get("non_negotiable_invariants", {})
        if inv.get("human_authority") != org.get("human_authority"):
            errors.append("Human authority drifted from Core alignment contract")
        if inv.get("virtual_seats") != role_count:
            errors.append("virtual seat count drifted from Core alignment contract")
        if inv.get("codex_role") != operating.get("codex") or inv.get("claude_role") != operating.get("claude_code"):
            errors.append("Human/AI role contract drifted from Core alignment")
        if inv.get("installation_equals_company_opening") is not False:
            errors.append("Core alignment must preserve installation != company opening")
    except Exception as exc:
        errors.append(f"Core alignment contract unreadable: {exc}")

    try:
        auto_cfg = json.loads(AUTOPILOT.read_text(encoding="utf-8-sig"))
        lock = json.loads(CORE_LOCK.read_text(encoding="utf-8-sig"))
        if auto_cfg.get("canonical_core_sha") != lock.get("baseline_sha"):
            errors.append("config/autopilot.json canonical Core SHA mismatch")
        if auto_cfg.get("supervisor", {}).get("bind_host") != "127.0.0.1" or auto_cfg.get("supervisor", {}).get("public_bind_forbidden") is not True:
            errors.append("Autopilot supervisor must be loopback-only")
    except Exception as exc:
        errors.append(f"Autopilot contract unreadable: {exc}")

    try:
        risk = json.loads(RISK_AUTHORITY.read_text(encoding="utf-8-sig"))
        if set(risk.get("levels", {})) != {"R0", "R1", "R2", "R3", "R4"}:
            errors.append("risk authority must define exactly R0-R4")
        if risk.get("invariants", {}).get("ai_may_self_approve_r3_or_r4") is not False:
            errors.append("AI self-approval of R3/R4 must be false")
    except Exception as exc:
        errors.append(f"risk authority policy unreadable: {exc}")

    return CompanyStatus(not errors, company_id, role_count, modes, errors)
