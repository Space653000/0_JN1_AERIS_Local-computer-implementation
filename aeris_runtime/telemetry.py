"""Truthful, evidence-backed telemetry for the AERIS five-plane service console."""
from __future__ import annotations

import json
import copy
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import LEDGER_PATH, verify_ledger
from .config import ROOT, load_config
from .evidence import validate_bundle
from .expected_runs import assess_all
from .knowledge import stats as knowledge_stats
from .machine import detect as machine_detect
from .router import ModelRouter
from .skills_runtime import list_skills
from .standards_registry import search_standards
from .workflow import list_workflow_templates, list_workflows

STATE = ROOT / ".aeris" / "state"
EVIDENCE = ROOT / ".aeris" / "evidence"
MATURITY = ROOT / "config" / "maturity.json"
SERVICE_PLANES={
    'CONTROL':('AERIS Orchestrator','Requirement / Task Store','Role / Pod Router','Workflow State Machine'),
    'KNOWLEDGE':('Constitution / Rules','Skill + Method Registry','Standards Registry','Memory + Knowledge'),
    'EXECUTION':('Local Model Router','Free Local Acoustic Baseline','Licensed Professional Tool Bus'),
    'TRUST':('Evidence Store','Verification Engine','Audit Ledger','Reproduction Runner'),
    'OPERATIONS':('Expected-run Health','Watchdog Recovery','Machine / GPU Qualification','Offline Continuity','Capability Maturity')}


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


def role_router_status(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Role counts report scope; they cannot certify qualified Pod routing."""
    total=snapshot.get('total_roles'); counts=snapshot.get('maturity_counts',{})
    values=[counts.get('L'+str(i)) for i in range(5)]
    if (type(total) is not int or total<0 or any(type(v) is not int or v<0 for v in values)
            or sum(values)!=total):
        raise ValueError('invalid or inconsistent role maturity telemetry')
    contracted=total-counts['L0']; executed=sum(counts[k] for k in ('L2','L3','L4'))
    accepted=counts['L3']+counts['L4']
    return _service('Role / Pod Router','CONTROL','FAILED' if counts['L0'] else 'DEGRADED',
        f'contracted_roles={contracted}; domain_execution_roles={executed}; role_domain_accepted={accepted}; '
        'registration/counts do not prove qualified independent routing acceptance',
        '/api/v1/capabilities','PARTIAL_DOMAIN_EXECUTION' if executed else 'CONTRACT_ONLY',snapshot.get('assessed_at_utc'))


def _collect_service_telemetry(control_summary: dict[str, int]) -> dict[str, Any]:
    """Assess capability evidence; process liveness alone never yields HEALTHY."""
    now = datetime.now(timezone.utc).isoformat()
    maturity = _read(MATURITY)
    skills = list_skills()
    try:
        from .engineering.api import live_matrix
        role_router=role_router_status(live_matrix())
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        role_router=_service('Role / Pod Router','CONTROL','FAILED',
            'Current role maturity unavailable: '+str(exc),'/api/v1/capabilities','UNKNOWN',now)
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
    required_skills = {"measurement-import-validation", "frequency-response-analysis", "requirement-verification", "free-local-acoustic-baseline", "pptx-beautify-lock-local"}
    registered_skills = {str(item.get("skill_id")) for item in skills}
    registry_ok = required_skills <= registered_skills
    reproduction_reports = [_read(path) for path in (ROOT / ".aeris" / "reproduction").glob("*/REPRODUCTION_REPORT.json")] if (ROOT / ".aeris" / "reproduction").exists() else []
    successful_reproductions = [item for item in reproduction_reports if item.get("result") == "PASS" and item.get("deterministic_result_match") is True]
    store_path = ROOT / ".aeris" / "control" / "control.sqlite3"
    store_ok = store_path.is_file() and {"projects", "tasks"} <= set(control_summary)
    rules_path = ROOT / "config" / "core_alignment.json"
    rules_ok = bool(_read(rules_path).get("canonical_core", {}).get("reviewed_sha"))
    standards = search_standards("")

    services = [
        _service("AERIS Orchestrator", "CONTROL", "HEALTHY" if opening.get("operational_state") == "OPEN_VERIFIED_SCOPE" else "DEGRADED", f"opening={opening.get('operational_state','UNKNOWN')}; projects={control_summary['projects']}; tasks={control_summary['tasks']}", str(opening_path.relative_to(ROOT)), "TESTED", _mtime(opening_path)),
        _service("Requirement / Task Store", "CONTROL", "HEALTHY" if store_ok else "FAILED", f"SQLite query succeeded={store_ok}; task_records={control_summary.get('tasks',0)}", str(store_path.relative_to(ROOT)), "TESTED", _mtime(store_path)),
        role_router,
        _service("Workflow State Machine", "CONTROL", "HEALTHY" if templates and evidenced_workflows else "DEGRADED" if templates else "NOT_CONFIGURED", f"templates={len(templates)}; instantiated_runs={len(workflows)}; evidenced_runs={len(evidenced_workflows)}", ".aeris/workflows", "TESTED", _mtime(ROOT/'.aeris/workflows')),
        _service("Constitution / Rules", "KNOWLEDGE", "HEALTHY" if rules_ok else "FAILED", f"versioned Core alignment parse valid={rules_ok}", "config/core_alignment.json", "TESTED", _mtime(rules_path)),
        _service("Skill + Method Registry", "KNOWLEDGE", "HEALTHY" if registry_ok else "DEGRADED" if skills else "NOT_CONFIGURED", f"skills={len(skills)}; required_local_registry_complete={registry_ok}", "skills", "IMPLEMENTED_NOT_PROFESSIONALLY_VERIFIED", now),
        _service("Standards Registry", "KNOWLEDGE", "DEGRADED" if standards else "NOT_CONFIGURED", f"metadata_records={len(standards)}; licensed full text is not implied", "standards/registry.v1.json", "METADATA_BASELINE", _mtime(ROOT/'standards/registry.v1.json')),
        _service("Memory + Knowledge", "KNOWLEDGE", "HEALTHY" if knowledge.get("documents", 0) else "NOT_CONFIGURED", f"indexed_documents={knowledge.get('documents',0)}", ".aeris/knowledge/knowledge.sqlite3", "TESTED", _mtime(ROOT/'.aeris/knowledge/knowledge.sqlite3')),
        _service("Local Model Router", "EXECUTION", "HEALTHY" if local_ok else "DEGRADED", str(local_reason), "config/aeris.yaml", "RUNTIME_PROBED", now),
        _service("Free Local Acoustic Baseline", "EXECUTION", "HEALTHY" if free_skill and any(item.get("execution", {}).get("skill_id") == "free-local-acoustic-baseline" for item in evidenced_workflows) else "DEGRADED" if free_skill else "NOT_CONFIGURED", f"registered={bool(free_skill)}; evidenced_runs={sum(item.get('execution',{}).get('skill_id') == 'free-local-acoustic-baseline' for item in evidenced_workflows)}; not licensed-professional verification", ".aeris/workflows", "FREE_BASELINE", _mtime(ROOT/'.aeris/workflows')),
        _service("Licensed Professional Tool Bus", "EXECUTION", "BLOCKED", "COMSOL/MATLAB/APx/KLIPPEL/SoundCheck/ACQUA licenses or devices unavailable", "config/maturity.json", "LICENSED_PROFESSIONAL_UNAVAILABLE", _mtime(MATURITY)),
        _service("Evidence Store", "TRUST", "HEALTHY" if valid_evidence else "NOT_CONFIGURED", f"sealed_valid_bundles={len(valid_evidence)}; candidate_bundles={len(evidence_dirs)}", ".aeris/evidence", "TESTED", _mtime(EVIDENCE)),
        _service("Verification Engine", "TRUST", "HEALTHY" if evidenced_workflows else "NOT_CONFIGURED", f"evidenced_or_verified_runs={len(evidenced_workflows)}; verified_runs={len(verified_workflows)}; per-run gates remain authoritative", ".aeris/workflows", "TESTED", _mtime(ROOT/'.aeris/workflows')),
        _service("Audit Ledger", "TRUST", "HEALTHY" if audit.get("valid") else "FAILED", f"valid={audit.get('valid')}; records={audit.get('records',0)}", str(LEDGER_PATH.relative_to(ROOT)), "TESTED", _mtime(LEDGER_PATH)),
        _service("Reproduction Runner", "TRUST", "HEALTHY" if successful_reproductions else "DEGRADED" if valid_evidence else "NOT_CONFIGURED", f"successful deterministic replays={len(successful_reproductions)}; valid sealed inputs={len(valid_evidence)}", ".aeris/reproduction", "TESTED", _mtime(ROOT/'.aeris/reproduction')),
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


class TelemetryProjection:
    """Single-flight full verification outside the HTTP response path.

    A collected snapshot is bounded by assessment *start* time, not completion:
    a slow probe cannot extend stale HEALTHY states by finishing much later.
    Pending, expired, changed-context and failed assessments remain explicit.
    """
    def __init__(self,collector,*,clock=time.monotonic):
        self.collector=collector; self.clock=clock
        self.lock=threading.Lock(); self.worker=None; self.snapshot=None
        self.running=False; self.requested=None
        self.snapshot_at=None; self.snapshot_key=None; self.error=None
        self.refresh_after_s=2.0; self.max_age_s=10.0

    def _refresh(self,summary,key,started):
        while True:
            try:
                result=self.collector(summary); error=None
            except Exception as exc:
                result=None; error=type(exc).__name__
            with self.lock:
                self.snapshot=result; self.snapshot_at=started
                self.snapshot_key=key; self.error=error
                if self.requested is not None and self.requested[1]!=key:
                    summary,key=self.requested; started=self.clock()
                else:
                    self.running=False
                    return

    def get(self,summary):
        key=tuple(sorted(summary.items()))
        with self.lock:
            now=self.clock(); age=None if self.snapshot_at is None else max(0.0,now-self.snapshot_at)
            matching=self.snapshot_key==key
            self.requested=(dict(summary),key)
            busy=self.running
            if not busy and (not matching or age is None or age>=self.refresh_after_s):
                self.running=True
                self.worker=threading.Thread(target=self._refresh,args=(dict(summary),key,now),daemon=True,
                                             name='aeris-service-telemetry')
                self.worker.start(); busy=True
            fresh=matching and age is not None and age<=self.max_age_s
            if fresh and self.snapshot is not None:
                result=copy.deepcopy(self.snapshot)
            else:
                state='FAILED' if fresh and self.error else 'CHECKING'
                reason=('Telemetry assessment failed: '+self.error if state=='FAILED' else
                        'Full evidence/runtime assessment pending or expired; no current health claim')
                rows=[_service(name,plane,state,reason,None,'UNKNOWN',None)
                      for plane,names in SERVICE_PLANES.items() for name in names]
                result={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'planes':list(SERVICE_PLANES),
                        'services':rows,'state_counts':{state:len(rows)},
                        'truth':'HEALTHY requires capability evidence; process-alive alone is insufficient.'}
            result.update(snapshot_age_s=age if matching else None,snapshot_max_age_s=self.max_age_s,
                          refresh_in_progress=busy,assessment_complete=fresh and self.snapshot is not None)
            return result

    def wait_for_refresh(self,timeout):
        """Bounded synchronization for CLI acceptance/tests; HTTP never waits."""
        with self.lock: worker=self.worker
        if worker is None: return True
        worker.join(timeout)
        return not worker.is_alive()


_SERVICE_PROJECTION=TelemetryProjection(_collect_service_telemetry)


def service_telemetry(control_summary: dict[str, int]) -> dict[str, Any]:
    return _SERVICE_PROJECTION.get(control_summary)


def wait_for_service_telemetry(timeout=15):
    """CLI/test synchronization; the HTTP response never uses this wait."""
    return _SERVICE_PROJECTION.wait_for_refresh(timeout)
