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
    errors=[]
    try: data=load_company_manifest(path)
    except Exception as exc: return CompanyStatus(False,"UNKNOWN",0,[],[f"manifest unreadable: {exc}"])
    company_id=str(data.get("company_id",""))
    if company_id!="AERIS": errors.append("company_id must be AERIS")
    org=data.get("organization",{}); role_count=int(org.get("virtual_role_count",0) or 0)
    if role_count!=100: errors.append("virtual_role_count must be 100")
    role_path=ROOT/org.get("role_registry","company/organization/roles.v1.json")
    try:
        role_data=json.loads(role_path.read_text(encoding="utf-8")); groups=role_data.get("groups",{}); actual=sum(len(v) for v in groups.values())
        if actual!=100: errors.append(f"role registry must contain 100 roles, found {actual}")
    except Exception as exc: errors.append(f"role registry unreadable: {exc}")
    modes=list(data.get("runtime",{}).get("modes",[]))
    if not {"offline","local","cloud","auto"}.issubset(set(modes)): errors.append("runtime modes incomplete")
    if not str(data.get("core_target",{}).get("authority","")).startswith("read_only"): errors.append("core target must be read_only")
    privacy=data.get("privacy",{})
    if privacy.get("local_data_cloud_egress")!="DENY": errors.append("local data cloud egress must be DENY")
    return CompanyStatus(not errors,company_id,role_count,modes,errors)
