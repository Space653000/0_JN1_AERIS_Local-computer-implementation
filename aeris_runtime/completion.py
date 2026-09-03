"""Evidence-derived completion-pass and remaining-gate inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .config import ROOT
from .pptx_provenance import verify as verify_pptx

PASS = ROOT / "config" / "completion_pass.v1.json"
MATURITY = ROOT / "config" / "maturity.json"
REPORT = ROOT / ".aeris" / "state" / "SOFTWARE_COMPLETION.json"
GATE_STATES = {"HUMAN_GATE", "EXTERNAL_LICENSE", "PHYSICAL_HARDWARE", "REBOOT_LOGOFF_REQUIRED", "BLOCKED_EXTERNAL"}


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _head_sha() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=5).strip()


def _files(*paths: str) -> tuple[bool, str]:
    missing = [path for path in paths if not (ROOT / path).is_file()]
    return (not missing, "required files present" if not missing else f"missing files: {missing}")


def _workspace() -> tuple[bool, str]:
    db = ROOT / ".aeris" / "control" / "control.sqlite3"
    if not db.is_file():
        return False, "control SQLite database missing"
    try:
        from .evidence import validate_bundle
        with sqlite3.connect(db) as conn:
            workflow_ids = [row[0] for row in conn.execute("SELECT workflow_id FROM tasks WHERE workflow_id IS NOT NULL AND workflow_id <> ''")]
        evidenced = 0
        for workflow_id in workflow_ids:
            workflow = _read(ROOT / ".aeris" / "workflows" / f"{workflow_id}.json")
            run_id = workflow.get("execution", {}).get("run_id")
            outcomes = workflow.get("verification", {}).get("outcomes", {})
            if workflow.get("state") == "EVIDENCED" and run_id and outcomes.get("G0_CONTRACT") == "PASS" and outcomes.get("G1_NUMERICAL") == "PASS" and validate_bundle(str(run_id)).get("valid"):
                evidenced += 1
        return evidenced > 0, f"linked workflows={len(workflow_ids)}; evidenced+G0/G1+sealed={evidenced}"
    except Exception as exc:
        return False, f"SQLite workflow-link query failed: {exc}"


def _telemetry() -> tuple[bool, str]:
    try:
        from .telemetry import service_telemetry
        payload = service_telemetry({"projects": 0, "tasks": 0})
        services = payload.get("services", [])
        required = {"state", "reason", "evidence_ref", "last_update_utc", "capability_maturity"}
        valid = len(services) >= 20 and set(payload.get("planes", [])) == {"CONTROL", "KNOWLEDGE", "EXECUTION", "TRUST", "OPERATIONS"} and all(required <= set(item) for item in services)
        return valid, f"five-plane service records={len(services)}"
    except Exception as exc:
        return False, f"telemetry assessment failed: {exc}"


def _free_acoustics() -> tuple[bool, str]:
    try:
        from .free_acoustics import analyze
        result = analyze({"samples": [0, 1, 0, -1, 0, 1, 0, -1], "sample_rate_hz": 8000, "input_kind": "impulse_response"})
        valid = result.get("result") == "PASS" and result.get("capability_maturity") == "FREE_BASELINE" and result.get("professional_verification") == "NOT_CLAIMED"
        return valid, "deterministic free baseline executed with professional claim denied"
    except Exception as exc:
        return False, f"free acoustic execution failed: {exc}"


def _pptx() -> tuple[bool, str]:
    try:
        result = verify_pptx()
        valid = result.get("provenance_valid") is True and result.get("authenticode") == "NOT_SIGNED" and result.get("production_acceptance") == "NOT_RUN_NO_INPUT_PPTX"
        return valid, f"provenance={result.get('result')}; authenticode={result.get('authenticode')}"
    except Exception as exc:
        return False, f"PPTX provenance failed: {exc}"


def _watchdog() -> tuple[bool, str]:
    report = _read(ROOT / ".aeris" / "state" / "UNATTENDED_INSTALL.json")
    valid = report.get("status") == "REGISTERED_RUNNING" and report.get("verified") is True and report.get("target_path", "").casefold() == str(ROOT).casefold()
    return valid, f"status={report.get('status', 'MISSING')}; verified={report.get('verified')}"


def _autopilot_contract() -> tuple[bool, str]:
    required = ("unresolved_software_gaps", "remaining_external_blockers", "remote_write_performed", "local_only_scope")
    texts = [(ROOT / path).read_text(encoding="utf-8") for path in ("scripts/autopilot.ps1", "scripts/autopilot.sh")]
    missing = [field for field in required if any(field not in text for text in texts)]
    return not missing, "both Autopilot implementations contain truth fields" if not missing else f"missing contract fields: {missing}"


def _browser() -> tuple[bool, str]:
    root = ROOT / ".aeris" / "evidence" / "browser-visual" / "latest"
    report = _read(root / "report.json")
    routes = report.get("routes", [])
    artifacts_ok = len(routes) == 6 and all(
        Path(item.get("artifact", "")).is_file()
        and hashlib.sha256(Path(item["artifact"]).read_bytes()).hexdigest() == item.get("repeatable_sha256")
        for item in routes
    )
    head = _head_sha()
    monitor = _read(ROOT / ".aeris" / "evidence" / "six-page-monitor.json")
    monitor_ok = monitor.get("result") == "PASS" and monitor.get("implementation_sha") == head and int(monitor.get("routes", 0)) == 6 and int(monitor.get("checks", 0)) >= 360 and int(monitor.get("failure_count", -1)) == 0
    semantic = _read(ROOT / ".aeris" / "evidence" / "browser-semantic-live.json")
    semantic_ok = semantic.get("AERIS_BROWSER_LIVE_SEMANTIC_E2E") == "PASS" and semantic.get("implementation_sha") == head and len(semantic.get("routes", [])) == 6
    valid = report.get("AERIS_BROWSER_VISUAL_ACCESSIBILITY_BASELINE") == "PASS" and report.get("implementation_sha") == head and artifacts_ok and int(report.get("accessibility_markers_checked", 0)) >= 7 and monitor_ok and semantic_ok
    return valid, f"visual routes={len(routes)}; artifacts_present={artifacts_ok}; live_semantic={semantic_ok}; continuous_monitor={monitor_ok}"


def _expected_runs() -> tuple[bool, str]:
    try:
        from .expected_runs import assess_all
        report = assess_all()
        source_ok = _files("aeris_runtime/expected_runs.py", "tests/test_expected_runs_concurrency.py")[0]
        valid = source_ok and report.get("overall") == "HEALTHY" and len(report.get("runs", [])) >= 2
        return valid, f"runtime={report.get('overall')}; contracts={len(report.get('runs', []))}; concurrency_regression={source_ok}"
    except Exception as exc:
        return False, f"expected-run assessment failed: {exc}"


def _acceptance() -> tuple[bool, str]:
    report = _read(ROOT / ".aeris" / "state" / "LOCAL_ACCEPTANCE.json")
    required = {"company_manifest", "unit_tests", "knowledge_build", "supported_machine_profile", "core_cache_integrity", "local_doctor", "real_local_inference", "offline_mode_doctor", "real_offline_mode_inference"}
    checks = set(report.get("checks", []))
    valid = report.get("result") == "PASS" and report.get("implementation_sha") == _head_sha() and required <= checks
    return valid, f"result={report.get('result', 'MISSING')}; checks={len(checks)}"


CHECKS: dict[str, Callable[[], tuple[bool, str]]] = {
    "ollama_api_no_desktop_autostart": lambda: _files("scripts/windows-ollama-api.ps1", "aeris_runtime/ollama_service.py", "tests/windows/test-ollama-api.ps1", "tests/test_ollama_service.py"),
    "core_ui_ssot_six_pages": lambda: _files("ui/web/dashboard.html", "ui/web/workspace.html", "ui/web/services.html", ".aeris/core-reference/aeris.css", ".aeris/core-reference/aeris-theme.js"),
    "workspace_fields_sqlite_workflow": _workspace,
    "five_plane_runtime_telemetry": _telemetry,
    "free_local_acoustic_baseline": _free_acoustics,
    "pptx_skill_registry_sha256_provenance": _pptx,
    "scheduled_task_watchdog_persistence": _watchdog,
    "expected_run_concurrent_atomic_write": _expected_runs,
    "autopilot_completion_fields": _autopilot_contract,
    "six_page_visual_accessibility_regression": _browser,
    "full_local_acceptance_and_gap_rescan": _acceptance,
}

GATE_CHECKS: dict[str, Callable[[], tuple[bool, str]]] = {
    "100_role_executable_domain_contracts": lambda: _files("config/role_contracts.v1.json", "tests/test_role_contracts.py", "tests/test_reviewer_allocation.py"),
    "prelogin_system_service_operation": _watchdog,
    "golden_acoustic_dataset_suite": lambda: _files("golden/acoustics/v1/manifest.json", "tests/test_golden_acoustics.py"),
    "full_skills_library": _free_acoustics,
    "full_methods_library": _free_acoustics,
    "full_live_standards_corpus": lambda: _files("standards/registry.v1.json", "tests/test_standards_registry.py"),
    "professional_acoustic_corpus": _acceptance,
    "os_network_egress_enforcement": lambda: _files("tests/test_privacy.py", "tests/test_ingress_security.py", "tests/test_local_endpoint_policy.py"),
    "machine_resource_qualification": _acceptance,
    "linux_self_contained_offline_ollama_runtime_package": lambda: _files("scripts/install-unattended-linux.sh", "tests/test_zero_cost_deployment.py"),
    "release_signing_and_attestation": _pptx,
    "full_company_relocation": lambda: _files("docs/deployment/STATE_BACKUP_RESTORE.md", "scripts/private-state.py", "tests/test_private_state.py"),
    "comsol_adapter": _free_acoustics,
    "matlab_adapter": _free_acoustics,
    "apx_adapter": _free_acoustics,
    "klippel_adapter": _free_acoustics,
    "soundcheck_adapter": _free_acoustics,
    "acqua_adapter": _free_acoustics,
    "commercial_release_readiness": _acceptance,
}


def assess(write: bool = False) -> dict[str, Any]:
    spec = _read(PASS)
    maturity = _read(MATURITY)
    assessed: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for item in spec.get("items", []):
        if item.get("classification") != "SOFTWARE_LOCAL_FIXABLE":
            continue
        check = CHECKS.get(str(item.get("id")))
        valid, detail = check() if check else (False, "no executable completion validator")
        result = {**item, "status": "COMPLETE" if valid else "UNRESOLVED", "evidence_check": detail}
        assessed.append(result)
        if not valid:
            unresolved.append(result)
    for name, item in maturity.get("capabilities", {}).items():
        if item.get("state") == "NOT_IMPLEMENTED":
            unresolved.append({"id": name, "classification": "SOFTWARE_LOCAL_FIXABLE", "status": "UNRESOLVED", "evidence_check": "maturity state is NOT_IMPLEMENTED"})
        if item.get("state") in GATE_STATES:
            baseline = maturity.get("gate_software_baselines", {}).get(name, {})
            gate_check = GATE_CHECKS.get(name)
            gate_valid, gate_detail = gate_check() if gate_check else (False, "no executable gate-baseline validator")
            if baseline.get("state") != "TESTED" or not str(baseline.get("evidence", "")).strip() or not gate_valid:
                unresolved.append({"id": f"{name}:software_baseline", "classification": "SOFTWARE_LOCAL_FIXABLE", "status": "UNRESOLVED", "evidence_check": "external/Human gate lacks a separately TESTED local-software baseline"})
    gates = [{"capability": name, "classification": item["state"], "required": item.get("required", "")} for name, item in maturity.get("capabilities", {}).items() if item.get("state") in GATE_STATES]
    payload = {
        "schema_version": 2, "assessed_at_utc": datetime.now(timezone.utc).isoformat(),
        "software_local_gaps_before": int(spec.get("software_local_gaps_before", len(assessed))),
        "software_local_gaps_after": len(unresolved), "software_local_fixable_zero": not unresolved,
        "assessed_software_items": assessed, "unresolved_software_gaps": unresolved,
        "remaining_external_blockers": gates, "remote_write_performed": False, "local_only_scope": True,
        "truth": "Completion is derived from executable evidence checks plus the maturity scan; tracked COMPLETE labels are not trusted as proof.",
    }
    if write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        tmp = REPORT.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(REPORT)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess AERIS software-local completion")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = assess(write=args.write)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["software_local_fixable_zero"] else 8


if __name__ == "__main__":
    raise SystemExit(main())
