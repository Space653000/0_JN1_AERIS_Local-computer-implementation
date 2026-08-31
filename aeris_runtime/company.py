"""Portable-company manifest validation for AERIS."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from .config import ROOT

MANIFEST = ROOT / "company" / "company.manifest.json"

@dataclass
class CompanyStatus:
    valid: bool
    company_id: str
    role_count: int
    modes: list[str]
    errors: list[str]

def load_company_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def validate_company_manifest(path: Path = MANIFEST) -> CompanyStatus:
    errors: list[str] = []
    try:
        data = load_company_manifest(path)
    except Exception as exc:
        return CompanyStatus(False, "UNKNOWN", 0, [], [f"manifest unreadable: {exc}"])
    company_id = str(data.get("company_id", ""))
    if company_id != "AERIS": errors.append("company_id must be AERIS")
    role_count = int(data.get("organization", {}).get("virtual_role_count", 0) or 0)
    if role_count != 100: errors.append("virtual_role_count must be 100")
    modes = list(data.get("runtime", {}).get("modes", []))
    required_modes = {"offline", "local", "cloud", "auto"}
    if not required_modes.issubset(set(modes)): errors.append("runtime modes incomplete")
    if data.get("core_target", {}).get("authority") != "read_only": errors.append("core target must be read_only")
    if data.get("runtime", {}).get("offline_cloud_calls") != "deny": errors.append("offline cloud calls must be denied")
    return CompanyStatus(not errors, company_id, role_count, modes, errors)
