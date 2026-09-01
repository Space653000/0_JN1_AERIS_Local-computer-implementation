"""Truthful, evidence-backed telemetry for the AERIS five-plane service console."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import LEDGER_PATH, verify_ledger
from .config import ROOT, load_config
from .evidence import validate_bundle
from .expected_runs import assess_all
from .knowledge import stats as knowledge_stats
from .machine import detect as machine_detect
from .roles import list_roles
from .router import ModelRouter
from .skills_runtime import list_skills
from .standards_registry import search_standards
from .workflow import list_workflow_templates, list_workflows

STATE = ROOT / ".aeris" / "state"
EVIDENCE = ROOT / ".aeris" / "evidence"
MATURITY = ROOT / "config" / "maturity.json"


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def _service(name: str, plane: str, state: str, reason: str, evidence_ref: str | None,
             maturity: str, last_update: str | None = None) -> dict[str, Any]:
    return {
        "service": name, "plane": plane, "state": state, "reason": reason,
        "evidence_ref": evidence_ref, "last_update_utc": last_update,
        "capability_maturity": maturity,
    }


def service_telemetry(control_summary: dict[str, int]) -> dict[str, Any]:
    """Assess capability evidence; process liveness alone never yields HEALTHY."""
    now = datetime.now(timezone.utc).isoformat()
    maturity = _read(MATURITY)
    roles, skills = list_roles(), list_skills()
    templates, workflows = list_workflow_templates(), list_workflows()
    knowledge = knowledge_stats()
    expected = assess_all()
    audit = verify_ledger()
    machine = machine_detect()
    watchdog_path = STATE / "UNATTENDED_OPERATIONS.json"
    watchdog = _read(watchdog_path)
    opening_path = STATE / "COMPANY_OPENING.json"
    opening = _read(opening_path)
    config = load_config()
    local_ok, local_reason = ModelRouter(config).local.health()
    evidence_dirs = [p for p in EVIDENCE.iterdir() if p.is_dir() and p.name.startswith("RUN-")] if EVIDENCE.exists() else []
    valid_evidence = [p for p in evidence_dirs if validate_bundle(p.name).get("valid")]
    evidenced_workflows = [item for item in workflows if item.get("state") in {"EVIDENCED", "VERIFIED"}]
    verified_workflows = [item for item in workflows if item.get("state") == "VERIFIED"]
    free_skill = next((item for item in skills if item.get("skill_id") == "free-local-acoustic-baseline"), None)
    store_path = ROOT / ".aeris" / "control" / "control.sqlite3"
    store_ok = store_path.is_file() and {"projects", "tasks"} <= set(control_summary)
    rules_path = ROOT / "config" / "core_alignment.json"
    rules_ok = bool(_read(rules_path).get("canonical_core", {}).get("reviewed_sha"))
    standards = search_standards("")

    services = [
        _service("AERIS Orchestrator", "CONTROL", "HEALTHY" if opening.get("operational_state") == "OPEN_VERIFIED_SCOPE" else "DEGRADED", f"opening={opening.get('operational_state','UNKNOWN')}; projects={control_summary['projects']}; tasks={control_summary['tasks']}", str(opening_path.relative_to(ROOT)), "TESTED", _mtime(opening_path)),
        _service("Requirement / Task Store", "CONTROL", "HEALTHY" if store_ok else "FAILED", f"SQLite query succeeded={store_ok}; task_records={control_summary.get('tasks',0)}", str(store_path.relative_to(ROOT)), "TESTED", _mtime(store_path)),
        _service("Role / Pod Router", "CONTROL", "HEALTHY" if len(roles) == 100 else "FAILED", f"{len(roles)} executable capability contracts available", "company/organization/roles.v1.json", "TESTED", now),
        _service("Workflow State Machine", "CONTROL", "HEALTHY" if templates else "NOT_CONFIGURED", f"templates={len(templates)}; instantiated_runs={len(workflows)}", ".aeris/workflows", "TESTED", _mtime(ROOT/'.aeris/workflows')),
        _service("Constitution / Rules", "KNOWLEDGE", "HEALTHY" if rules_ok else "FAILED", f"versioned Core alignment parse valid={rules_ok}", "config/core_alignment.json", "TESTED", _mtime(rules_path)),
        _service("Skill + Method Registry", "KNOWLEDGE", "HEALTHY" if skills else "NOT_CONFIGURED", f"skills={len(skills)}", "skills", "IMPLEMENTED_NOT_PROFESSIONALLY_VERIFIED", now),
        _service("Standards Registry", "KNOWLEDGE", "DEGRADED" if standards else "NOT_CONFIGURED", f"metadata_records={len(standards)}; licensed full text is not implied", "standards/registry.v1.json", "METADATA_BASELINE", _mtime(ROOT/'standards/registry.v1.json')),
        _service("Memory + Knowledge", "KNOWLEDGE", "HEALTHY" if knowledge.get("documents", 0) else "NOT_CONFIGURED", f"indexed_documents={knowledge.get('documents',0)}", ".aeris/knowledge/knowledge.sqlite3", "TESTED", _mtime(ROOT/'.aeris/knowledge/knowledge.sqlite3')),
        _service("Local Model Router", "EXECUTION", "HEALTHY" if local_ok else "DEGRADED", str(local_reason), "config/aeris.yaml", "RUNTIME_PROBED", now),
        _service("Free Local Acoustic Baseline", "EXECUTION", "HEALTHY" if free_skill else "NOT_CONFIGURED", f"registered={bool(free_skill)}; deterministic adapter, not licensed-professional verification", "skills/free-local-acoustic-baseline/manifest.json", "FREE_BASELINE", _mtime(ROOT/'skills/free-local-acoustic-baseline/manifest.json')),
        _service("Licensed Professional Tool Bus", "EXECUTION", "BLOCKED", "COMSOL/MATLAB/APx/KLIPPEL/SoundCheck/ACQUA licenses or devices unavailable", "config/maturity.json", "LICENSED_PROFESSIONAL_UNAVAILABLE", _mtime(MATURITY)),
        _service("Evidence Store", "TRUST", "HEALTHY" if valid_evidence else "NOT_CONFIGURED", f"sealed_valid_bundles={len(valid_evidence)}; candidate_bundles={len(evidence_dirs)}", ".aeris/evidence", "TESTED", _mtime(EVIDENCE)),
        _service("Verification Engine", "TRUST", "HEALTHY" if evidenced_workflows else "NOT_CONFIGURED", f"evidenced_or_verified_runs={len(evidenced_workflows)}; verified_runs={len(verified_workflows)}; per-run gates remain authoritative", ".aeris/workflows", "TESTED", _mtime(ROOT/'.aeris/workflows')),
        _service("Audit Ledger", "TRUST", "HEALTHY" if audit.get("valid") else "FAILED", f"valid={audit.get('valid')}; records={audit.get('records',0)}", str(LEDGER_PATH.relative_to(ROOT)), "TESTED", _mtime(LEDGER_PATH)),
        _service("Reproduction Runner", "TRUST", "HEALTHY" if valid_evidence else "NOT_CONFIGURED", f"valid sealed replay inputs={len(valid_evidence)}", "aeris_runtime/reproduction.py", "TESTED", _mtime(ROOT/'aeris_runtime/reproduction.py')),
        _service("Expected-run Health", "OPERATIONS", "HEALTHY" if expected.get("overall") == "HEALTHY" else str(expected.get("overall", "UNKNOWN")), f"contracts={len(expected.get('runs',[]))}", ".aeris/state/EXPECTED_RUNS.json", "TESTED", now),
        _service("Watchdog Recovery", "OPERATIONS", str(watchdog.get("state", "UNKNOWN")), str(watchdog.get("action", "No watchdog evidence")), str(watchdog_path.relative_to(ROOT)), "TESTED", _mtime(watchdog_path)),
        _service("Machine / GPU Qualification", "OPERATIONS", "HEALTHY" if machine.get("qualification",{}).get("overall_state") == "QUALIFIED_BASELINE" else "DEGRADED", f"{machine.get('profile')}; GPU={machine.get('gpu')}; VRAM={machine.get('vram_gb')} GB", "config/machine_qualification.v1.json", "QUALIFIED_BASELINE", now),
        _service("Offline Continuity", "OPERATIONS", "HEALTHY" if local_ok and config.mode in {"local", "offline"} else "DEGRADED", f"mode={config.mode}; provider_ready={local_ok}; hard network isolation is separately evidenced", "config/zero_cost_no_claude.v1.json", "LOCAL_RUNTIME_VERIFIED_SCOPE", now),
        _service("Capability Maturity", "OPERATIONS", "DEGRADED", f"product_stage={maturity.get('product_stage','UNKNOWN')}; green service states do not imply company completion", "config/maturity.json", "TRUTH_PROJECTION", _mtime(MATURITY)),
    ]
    counts: dict[str, int] = {}
    for item in services:
        counts[item["state"]] = counts.get(item["state"], 0) + 1
    return {"generated_at_utc": now, "planes": ["CONTROL", "KNOWLEDGE", "EXECUTION", "TRUST", "OPERATIONS"], "services": services, "state_counts": counts, "truth": "HEALTHY requires capability evidence; process-alive alone is insufficient."}
