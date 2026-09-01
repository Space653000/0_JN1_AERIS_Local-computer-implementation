"""Independent-review evidence aggregator for Claude Code acceptance."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import append_event, verify_ledger
from .company import validate_company_manifest
from .config import ROOT, load_config
from .corecache import verify_core_cache
from .machine import detect as machine_detect
from .operations import ACCEPTANCE_FILE, OPENING_FILE, supervisor_status

STATE_DIR = ROOT / ".aeris" / "state"
CLAUDE_TESTS_FILE = STATE_DIR / "CLAUDE_TESTS.json"
CLAUDE_REPORT_FILE = STATE_DIR / "CLAUDE_ACCEPTANCE.json"


def _read(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=5).strip()
    except Exception:
        return "UNKNOWN"


def _versioned_worktree_dirty() -> tuple[bool, str]:
    try:
        out = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"], text=True, timeout=5).strip()
        return bool(out), out
    except Exception as exc:
        return True, f"unable to inspect worktree: {exc}"


def independent_acceptance(reviewer: str = "Claude Code") -> dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    company = validate_company_manifest()
    core = verify_core_cache()
    machine = machine_detect()
    config = load_config()
    audit = verify_ledger()
    acceptance = _read(ACCEPTANCE_FILE)
    opening = _read(OPENING_FILE)
    tests = _read(CLAUDE_TESTS_FILE)
    supervisor = supervisor_status()
    dirty, dirty_detail = _versioned_worktree_dirty()

    failures: list[str] = []
    blockers: list[str] = []
    limits: list[str] = []

    if not company.valid:
        failures.append("COMPANY_MANIFEST_INVALID")
    if not core.get("valid"):
        failures.append("CORE_CACHE_INTEGRITY_FAIL")
    if not audit.get("valid"):
        failures.append("AUDIT_LEDGER_INVALID")
    if dirty:
        failures.append("VERSIONED_IMPLEMENTATION_WORKTREE_DIRTY")
    if not tests:
        blockers.append("CLAUDE_TEST_REPORT_MISSING")
    elif tests.get("result") != "PASS":
        failures.append("DETERMINISTIC_TESTS_FAILED")
    else:
        drift_state = str(tests.get("remote_core_drift_gate", "NOT_TESTED"))
        if drift_state == "FAIL":
            failures.append("REMOTE_CANONICAL_CORE_DRIFT_DETECTED")
        elif drift_state != "PASS":
            limits.append("REMOTE_CANONICAL_CORE_DRIFT_NOT_LIVE_VERIFIED")

    if not machine.get("supported_baseline"):
        blockers.append("UNSUPPORTED_MACHINE_PROFILE")
    if not acceptance:
        limits.append("REAL_MACHINE_ACCEPTANCE_NOT_PRESENT")
    elif acceptance.get("result") != "PASS":
        failures.append("REAL_MACHINE_ACCEPTANCE_FAILED")
    if not opening:
        limits.append("COMPANY_OPENING_REPORT_NOT_PRESENT")
    elif opening.get("operational_state") == "BLOCKED":
        failures.append("COMPANY_OPENING_BLOCKED")
    if not supervisor.get("reachable"):
        limits.append("LOCAL_SUPERVISOR_NOT_REACHABLE")
    if acceptance and acceptance.get("hard_offline_network_state") == "NOT_TESTED":
        limits.append("HARD_OFFLINE_NOT_TESTED")

    if failures:
        result = "FAIL"
    elif blockers:
        result = "BLOCKED"
    elif limits:
        result = "PASS_WITH_LIMITS"
    else:
        result = "PASS"

    payload = {
        "schema_version": 1,
        "reviewer": reviewer,
        "reviewer_role": "independent_reviewer",
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "final_result": result,
        "canonical_core_sha": core.get("core_sha") or (_read(ROOT / "core.lock.json") or {}).get("baseline_sha"),
        "implementation_sha": _git_sha(),
        "local_target_path": str(ROOT),
        "machine_profile": machine.get("profile"),
        "runtime_mode": config.mode,
        "private_endpoint_scope": config.local_network_scope,
        "unit_test_result": tests.get("result") if tests else "NOT_RECORDED",
        "remote_core_drift_gate": tests.get("remote_core_drift_gate") if tests else "NOT_RECORDED",
        "core_integrity_result": "PASS" if core.get("valid") else "FAIL",
        "audit_integrity_result": "PASS" if audit.get("valid") else "FAIL",
        "local_inference_result": acceptance.get("result") if acceptance else "NOT_TESTED",
        "offline_result": acceptance.get("result") if acceptance else "NOT_TESTED",
        "hard_offline_result": acceptance.get("hard_offline_network_state", "NOT_TESTED") if acceptance else "NOT_TESTED",
        "company_opening_state": opening.get("operational_state") if opening else "NOT_OPENED",
        "supervisor": supervisor,
        "versioned_worktree_dirty": dirty,
        "versioned_worktree_detail": dirty_detail,
        "failures": failures,
        "blockers": blockers,
        "limits": sorted(set(limits)),
        "evidence_paths": {
            "tests": str(CLAUDE_TESTS_FILE),
            "acceptance": str(ACCEPTANCE_FILE),
            "opening": str(OPENING_FILE),
            "audit": str(ROOT / ".aeris" / "audit" / "audit.jsonl"),
        },
        "truth": "This report is deterministic review evidence. Claude must still inspect raw evidence and challenge scope; it is not self-authenticating approval.",
    }
    CLAUDE_REPORT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_event("INDEPENDENT_ACCEPTANCE_RECORDED", reviewer, {"result": result, "failures": failures, "blockers": blockers, "limits": payload["limits"]})
    return payload
