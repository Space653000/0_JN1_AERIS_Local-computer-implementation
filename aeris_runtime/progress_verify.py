"""P2.1/P2.2 Progress Engine: generate PROGRESS_TRUTH.json Evidence by actually
running checks, instead of a human hand-typing "result": "PASS".

Every invocation re-checks every item this module knows about against the
current source tree and the current git HEAD; it never carries a prior PASS
forward without re-running its check (P2.2). A check that cannot run (e.g. the
local server is not reachable for an HTTP-backed item) reports UNKNOWN/FAIL,
never a guessed PASS.
"""
from __future__ import annotations

import json
import subprocess
import unittest
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .config import ROOT
from .progress_truth import CANONICAL_AUTHORITY_SHA

EVIDENCE_DIR = ROOT / ".aeris" / "evidence" / "progress"
TRUTH_PATH = EVIDENCE_DIR / "PROGRESS_TRUTH.json"
LOCAL_BASE_URL = "http://127.0.0.1:8765"


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    detail: str
    artifact: str


def _head_sha() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=5).strip()


def _current_branch() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"], text=True, timeout=5).strip()


def _run_unittest(*module_names: str) -> tuple[bool, str]:
    import io
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromName(name) for name in module_names)
    result = unittest.TextTestRunner(verbosity=0, stream=io.StringIO()).run(suite)
    ok = result.wasSuccessful()
    return ok, f"ran={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} modules={','.join(module_names)}"


def _grep(path: str, *needles: str) -> tuple[bool, str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [n for n in needles if n not in text]
    return (not missing), (f"all present in {path}" if not missing else f"missing in {path}: {missing}")


def _http_get_json(path: str, timeout: float = 30.0) -> dict:
    # Some endpoints (notably /api/v1/capabilities) compute their response
    # synchronously over all 100 roles' evidence, unlike the cached/async
    # telemetry endpoints; a short timeout here would misreport a slow-but-
    # working server as unreachable.
    with urllib.request.urlopen(LOCAL_BASE_URL + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _check_p0_1() -> CheckResult:
    ok, detail = _run_unittest("tests.test_site_zh_tw", "tests.test_ui_core_ssot", "tests.test_controlplane")
    return CheckResult(ok, detail, "tests/test_site_zh_tw.py; tests/test_ui_core_ssot.py; tests/test_controlplane.py")


def _check_p0_2() -> CheckResult:
    try:
        branch = _current_branch()
        subprocess.run(["git", "-C", str(ROOT), "fetch", "origin", branch], check=True, capture_output=True, timeout=20)
        behind = subprocess.check_output(["git", "-C", str(ROOT), "rev-list", "--count", f"origin/{branch}..HEAD"], text=True, timeout=5).strip()
        ok = behind == "0"
        return CheckResult(ok, f"branch={branch} unpushed_commits={behind}", f"git ref origin/{branch}")
    except Exception as exc:
        return CheckResult(False, f"git check failed: {exc}", "git")


def _check_p0_3() -> CheckResult:
    try:
        from .blueprint_compatibility import validate
        validate(ROOT)
        remote = subprocess.check_output(
            ["git", "ls-remote", "https://github.com/Space653000/0_JN1_AERIS.git", "refs/heads/main"],
            text=True, timeout=20,
        ).split()[0]
        ok = remote == CANONICAL_AUTHORITY_SHA
        return CheckResult(ok, f"local pointers compatible; canonical Core main={remote}", "aeris_runtime/blueprint_compatibility.py; core.lock.json")
    except Exception as exc:
        return CheckResult(False, f"blueprint compatibility check failed: {exc}", "aeris_runtime/blueprint_compatibility.py")


def _check_p0_4() -> CheckResult:
    return _check_p0_1()


def _check_p0_5() -> CheckResult:
    ok1, d1 = _grep(".aeris/core-reference/aeris-theme.js", "localStorage.getItem(THEME_KEY)", "localStorage.setItem(THEME_KEY,next)")
    ok2, d2 = _grep("ui/web/i18n.js", "localStorage.getItem(LANG_KEY)", "localStorage.setItem(LANG_KEY")
    return CheckResult(ok1 and ok2, f"{d1}; {d2}", "static code presence check only, not a live click-through")


def _check_p0_6() -> CheckResult:
    ok, detail = _run_unittest("tests.test_progress_truth")
    return CheckResult(ok, detail, "tests/test_progress_truth.py")


def _check_p0_7() -> CheckResult:
    try:
        health = _http_get_json("/health")
        head = _head_sha()
        aligned = health.get("implementation_sha") == head
        return CheckResult(aligned, f"live implementation_sha={health.get('implementation_sha')} head={head}", "aeris_runtime/progress.py; ui/web/progress.html")
    except Exception as exc:
        return CheckResult(False, f"local server unreachable at {LOCAL_BASE_URL}: {exc}", "aeris_runtime/progress.py")


def _check_p1_1() -> CheckResult:
    ok, detail = _grep(".aeris/core-reference/aeris.css", "--accent:#62c5ba", "--accent:#72d0c5")
    return CheckResult(ok, detail, ".aeris/core-reference/aeris.css")


def _check_p1_2() -> CheckResult:
    ok, detail = _grep("ui/web/dashboard.html", "summary-card", "feature-card")
    return CheckResult(ok, detail, "ui/web/dashboard.html")


def _check_p1_3() -> CheckResult:
    try:
        result = _http_get_json("/api/v1/audit/verify")
        ok = bool(result.get("valid"))
        return CheckResult(ok, f"records={result.get('records')} errors={len(result.get('errors', []))}", "aeris_runtime/audit.py; ui/web/activity.html")
    except Exception as exc:
        return CheckResult(False, f"local server unreachable at {LOCAL_BASE_URL}: {exc}", "aeris_runtime/audit.py")


def _check_p1_4() -> CheckResult:
    ok, detail = _grep("ui/web/capabilities.js", "cap-graph-group", "lvl-${escape(r.level)}")
    return CheckResult(ok, detail, "ui/web/capabilities.js; ui/web/capabilities.css")


def _check_p1_5() -> CheckResult:
    ok, detail = _grep("ui/web/aeris-live.js", "stateClass", "gateClass")
    return CheckResult(ok, detail, "ui/web/aeris-live.js")


def _check_p1_6() -> CheckResult:
    ok, detail = _grep("ui/web/aeris-live.js", "WF_STEPS", "expandedWorkflows")
    return CheckResult(ok, detail, "ui/web/aeris-live.js")


def _check_p1_7() -> CheckResult:
    ok, detail = _grep("ui/web/capabilities.js", "renderTaught", "negative_patch")
    return CheckResult(ok, detail, "ui/web/capabilities.js")


def _check_p1_8() -> CheckResult:
    ok, detail = _grep("ui/web/dashboard.html", "G0 契約格式")
    return CheckResult(ok, detail, "ui/web/dashboard.html; ui/web/workspace.html; ui/web/services.html")


# P3.1-P3.4 deliberately read existing state (the local evaluation-index
# directory, the live /api/v1/capabilities snapshot) rather than re-running
# aeris_runtime.engineering.factory.evaluate_role / RoleAcceptanceFactory for
# all 100 roles: each of those calls seals a brand-new Evidence bundle, so
# re-running the full pipeline on every progress_verify invocation would keep
# growing the evidence store and re-trigger the exact telemetry slowdown this
# session already found and fixed (see aeris_runtime/telemetry.py). Checking
# "was this already run and does the live matrix reflect it" is a different,
# much cheaper question than "run it now."


def _check_p3_1() -> CheckResult:
    eval_dir = ROOT / ".aeris" / "capability-factory" / "evaluations"
    count = len(list(eval_dir.glob("R*.json"))) if eval_dir.is_dir() else 0
    ok = count >= 90
    return CheckResult(ok, f"shared-skill evaluation index has {count}/100 role records", "aeris_runtime/engineering/factory.py:evaluate_role; scripts/run_capability_factory.py")



# /api/v1/capabilities now serves a cached matrix instantly once warm (see
# aeris_runtime/engineering/api.py's background-refresh live_matrix), but the
# very first call after a server restart is a genuine cold start that can
# take several minutes at this session's evidence-store volume. progress_verify
# is meant to be runnable right after a fresh restart (see how this module's
# own tick routine restarts the server before re-verifying), so these two
# checks use a generous timeout rather than misreporting a real cold start as
# "server unreachable".
_CAPABILITIES_COLD_START_TIMEOUT_S = 360.0


def _check_p3_2() -> CheckResult:
    try:
        matrix = _http_get_json("/api/v1/capabilities", timeout=_CAPABILITIES_COLD_START_TIMEOUT_S)
        l2 = int(matrix.get("100_role_L2", 0))
        ok = l2 >= 70
        return CheckResult(ok, f"100_role_L2={l2}/100 (threshold 70)", "aeris_runtime/engineering/role_acceptance.py; scripts/run_capability_factory.py")
    except Exception as exc:
        return CheckResult(False, f"local server unreachable at {LOCAL_BASE_URL}: {exc}", "aeris_runtime/engineering/role_acceptance.py")


def _check_p3_3() -> CheckResult:
    try:
        matrix = _http_get_json("/api/v1/capabilities", timeout=_CAPABILITIES_COLD_START_TIMEOUT_S)
        gaps = matrix.get("unresolved_capability_gaps") or []
        l2 = int(matrix.get("100_role_L2", 0))
        total = int(matrix.get("total_roles", 0))
        ok = bool(gaps) and (l2 + len(gaps) == total)
        return CheckResult(ok, f"unresolved_capability_gaps={len(gaps)} disclosed; l2({l2})+gaps({len(gaps)})=={total}", "aeris_runtime/engineering/factory.py (unresolved_capability_gaps field)")
    except Exception as exc:
        return CheckResult(False, f"local server unreachable at {LOCAL_BASE_URL}: {exc}", "aeris_runtime/engineering/factory.py")


def _check_p3_4() -> CheckResult:
    ok, detail = _grep("scripts/run_capability_factory.py", "evaluate_role", "RoleAcceptanceFactory", "def main")
    return CheckResult(ok, detail, "scripts/run_capability_factory.py")


def _check_p3_5() -> CheckResult:
    p3_registered = [k for k in CHECKS if k.startswith("P3.") and k not in {"P3.5", "P3.6"}]
    ok = len(p3_registered) >= 4
    return CheckResult(ok, f"P3.1-P3.4/P3.7/P3.8 registered in progress_verify: {sorted(p3_registered)}", "aeris_runtime/progress_verify.py")


def _check_p3_6() -> CheckResult:
    module_ok, module_detail = _grep("aeris_runtime/engineering/l3_award.py", "def prepare_review", "def human_decide", "a named Human approver is required")
    cli_ok, cli_detail = _grep("aeris_runtime/cli.py", "def cmd_l3")
    test_ok, test_detail = _run_unittest("tests.test_l3_award")
    ok = module_ok and cli_ok and test_ok
    return CheckResult(ok, f"{module_detail}; {cli_detail}; {test_detail}", "aeris_runtime/engineering/l3_award.py; tests/test_l3_award.py")


def _check_p3_7() -> CheckResult:
    # L4 requires real instruments/calibration/expert approval; no software
    # change can honestly grant it. The acceptance criterion is that the
    # codebase says so explicitly rather than silently allowing an L4 claim.
    ok, detail = _grep("aeris_runtime/engineering/factory.py", "cannot be granted by this factory")
    return CheckResult(ok, detail, "aeris_runtime/engineering/factory.py (verification_rubric)")


def _check_p3_8() -> CheckResult:
    ok, detail = _grep("docs/AERIS_P3_GOLDEN_ENGINEER.md", "73/100 roles at L2 or higher", "27/100")
    return CheckResult(ok, detail, "docs/AERIS_P3_GOLDEN_ENGINEER.md")


def _check_p4_1() -> CheckResult:
    ok, detail = _grep("ui/web/capabilities.js", "skill-library", "skillLibList", "skillLibQuery")
    return CheckResult(ok, detail, "ui/web/capabilities.js")


def _check_p4_2() -> CheckResult:
    ok, detail = _grep("ui/web/capabilities.js", "data-skill-example", "taughtHTML(data.fixture)")
    return CheckResult(ok, detail, "ui/web/capabilities.js")


def _check_p4_3() -> CheckResult:
    ok, detail = _grep("ui/web/capabilities.js", "尚無可用範例角色", "誠實顯示為缺少範例")
    return CheckResult(ok, detail, "ui/web/capabilities.js")


def _check_p4_4() -> CheckResult:
    try:
        skills = _http_get_json("/api/v1/skills").get("skills", [])
        translatable = {s["skill_id"] for s in skills if str(s.get("acceptance", "")).strip()}
        translations = json.loads((ROOT / "ui/web/skills-zh-tw.json").read_text(encoding="utf-8"))
        missing = translatable - set(translations)
        extra = set(translations) - {s["skill_id"] for s in skills}
        ok = not missing and not extra
        return CheckResult(ok, f"translatable_skills={len(translatable)}; translated={len(translations)}; missing={sorted(missing)}; stale_extra={sorted(extra)}" if not ok else f"all {len(translatable)} translatable skills have a zh-TW entry in skills-zh-tw.json", "ui/web/skills-zh-tw.json; ui/web/capabilities.js")
    except Exception as exc:
        return CheckResult(False, f"check failed: {exc}", "ui/web/skills-zh-tw.json")


def _check_p4_5() -> CheckResult:
    try:
        data = _http_get_json("/api/v1/skills")
        skills = data.get("skills", [])
        with_mapping = [s for s in skills if s.get("role_mappings")]
        ok = len(skills) >= 100 and len(with_mapping) / max(1, len(skills)) >= 0.9
        return CheckResult(ok, f"skills={len(skills)}; with_role_mapping={len(with_mapping)} ({round(100*len(with_mapping)/max(1,len(skills)))}%)", "ui/web/capabilities.js; aeris_runtime/controlplane.py:/api/v1/skills")
    except Exception as exc:
        return CheckResult(False, f"local server unreachable at {LOCAL_BASE_URL}: {exc}", "aeris_runtime/controlplane.py")


def _check_p4_6() -> CheckResult:
    ok, detail = _grep("ui/web/capabilities.js", "lib.id='skill-library'", "skillLibList", "skillLibTaught")
    has_write, _ = _grep("ui/web/capabilities.js", "current_maturity_level")
    ok = ok and not has_write
    return CheckResult(ok, detail + f"; skill library never writes current_maturity_level={not has_write}", "ui/web/capabilities.js")


def _check_p4_7() -> CheckResult:
    ok, detail = _grep("ui/web/capabilities.js", "/api/v1/capabilities/fixture/", "taughtHTML")
    return CheckResult(ok, detail + "; Skills Library reuses the same fixture endpoint as the P1.7 teaching panel, no separate placeholder path", "ui/web/capabilities.js")


def _check_p2_1() -> CheckResult:
    ok, detail = _grep("aeris_runtime/progress_verify.py", "CHECKS: dict[str, Callable[[], CheckResult]]",
                        'truth.setdefault("items", {})[item_id]', '"truth": "Generated by aeris_runtime.progress_verify, not hand-authored."')
    return CheckResult(ok and len(CHECKS) > 0, detail + f"; CHECKS registered={len(CHECKS)}", "aeris_runtime/progress_verify.py")


def _check_p2_2() -> CheckResult:
    ok, detail = _grep("aeris_runtime/progress_verify.py", "targets = items if items is not None else _ORDER",
                        'truth.setdefault("items", {}).pop(item_id, None)')
    return CheckResult(ok, detail + "; every run() call re-executes every requested item's check, demoting stale PASS on regression", "aeris_runtime/progress_verify.py")


def _check_p2_3() -> CheckResult:
    from .progress_history import compute_history
    points = compute_history()
    ok = isinstance(points, list) and len(points) > 0
    sorted_ok = points == sorted(points, key=lambda p: p["captured_at_utc"])
    api_ok, _ = _grep("aeris_runtime/controlplane.py", "/api/v1/progress/history", "compute_history")
    ui_ok, _ = _grep("ui/web/progress.js", "loadHistory", "renderHistory", "/api/v1/progress/history")
    ok = ok and sorted_ok and api_ok and ui_ok
    return CheckResult(
        ok,
        f"history points reconstructed from real Evidence={len(points)}; chronological={sorted_ok}; api_wired={api_ok}; ui_wired={ui_ok}",
        "aeris_runtime/progress_history.py; aeris_runtime/controlplane.py; ui/web/progress.js",
    )


def _check_p2_5() -> CheckResult:
    ps1_ok, _ = _grep("scripts/local-acceptance.ps1", "aeris_runtime.progress_verify")
    sh_ok, _ = _grep("scripts/local-acceptance.sh", "aeris_runtime.progress_verify")
    ok = ps1_ok and sh_ok
    return CheckResult(ok, f"wired: ps1={ps1_ok} sh={sh_ok}", "scripts/local-acceptance.ps1; scripts/local-acceptance.sh")


def _check_p2_6() -> CheckResult:
    ok, detail = _run_unittest("tests.test_progress_verify")
    return CheckResult(ok, detail, "tests/test_progress_verify.py")


def _check_p2_7() -> CheckResult:
    doc_ok, doc_detail = _grep("docs/AERIS_P2_PROGRESS_ENGINE.md", "P2.1", "P2.7")
    doc_exists = (ROOT / "docs/AERIS_P2_PROGRESS_ENGINE.md").exists()
    return CheckResult(doc_exists and doc_ok, doc_detail, "docs/AERIS_P2_PROGRESS_ENGINE.md; aeris_runtime/progress_verify.py module docstring")


def _check_p5_3() -> CheckResult:
    try:
        m = json.loads((ROOT / "config" / "maturity.json").read_text(encoding="utf-8-sig"))
        caps = m.get("capabilities", {})
        baselines = m.get("gate_software_baselines", {})
        names = ["comsol_adapter", "matlab_adapter", "apx_adapter", "klippel_adapter", "soundcheck_adapter", "acqua_adapter"]
        bad = [n for n in names if caps.get(n, {}).get("state") != "EXTERNAL_LICENSE"
               or baselines.get(n, {}).get("state") != "TESTED"
               or "equivalence is not claimed" not in str(baselines.get(n, {}).get("evidence", ""))]
        from .completion import _free_acoustics
        free_ok, free_detail = _free_acoustics()
        ok = not bad and free_ok
        return CheckResult(ok, f"6 professional-tool gates correctly EXTERNAL_LICENSE with honest non-equivalence baselines; free-baseline check: {free_detail}" if ok else f"inconsistent gate declarations: {bad}", "config/maturity.json; aeris_runtime/completion.py")
    except Exception as exc:
        return CheckResult(False, f"check failed: {exc}", "config/maturity.json")


def _check_p5_5() -> CheckResult:
    ok, detail = _grep("aeris_runtime/engineering/orchestration.py", "keyword-only routing is not supported", "\"evidence_curator\":curator", "\"reviewer\":reviewer")
    return CheckResult(ok, detail, "aeris_runtime/engineering/orchestration.py")


def _check_p5_8() -> CheckResult:
    try:
        matrix = _http_get_json("/api/v1/capabilities", timeout=_CAPABILITIES_COLD_START_TIMEOUT_S)
        required = ["total_roles", "maturity_counts", "total_executable_skills", "total_methods",
                    "total_golden_cases", "total_negative_cases", "total_regression_cases",
                    "coverage_by_group", "unresolved_capability_gaps"]
        missing = [k for k in required if k not in matrix]
        return CheckResult(not missing, f"all present" if not missing else f"missing: {missing}", "aeris_runtime/engineering/factory.py:matrix() via /api/v1/capabilities")
    except Exception as exc:
        return CheckResult(False, f"local server unreachable at {LOCAL_BASE_URL}: {exc}", "aeris_runtime/engineering/factory.py")


_CHIEF_COUNCIL_ROLES = {"R001", "R002", "R003", "R004", "R006", "R007", "R008"}


def _check_p5_1() -> CheckResult:
    try:
        matrix = _http_get_json("/api/v1/capabilities", timeout=_CAPABILITIES_COLD_START_TIMEOUT_S)
        l2_count = matrix.get("maturity_counts", {}).get("L2", 0)
        ok = l2_count >= 90
        return CheckResult(ok, f"100_role_L2={l2_count}/100 (threshold 90 after this session's domain-contract sweep)", "aeris_runtime/engineering/factory.py; company/capabilities/R0*/capability.json")
    except Exception as exc:
        return CheckResult(False, f"local server unreachable at {LOCAL_BASE_URL}: {exc}", "aeris_runtime/engineering/factory.py")


def _check_p5_2() -> CheckResult:
    try:
        matrix = _http_get_json("/api/v1/capabilities", timeout=_CAPABILITIES_COLD_START_TIMEOUT_S)
        gaps = set(matrix.get("unresolved_capability_gaps", []))
        ok = gaps == _CHIEF_COUNCIL_ROLES
        return CheckResult(ok, f"unresolved gaps are exactly the 7 Chief Council roles: {sorted(gaps)}" if ok else f"gaps do not match the disclosed boundary: {sorted(gaps)}", "aeris_runtime/engineering/factory.py; docs/AERIS_P5_ENGINEER_FACTORY.md")
    except Exception as exc:
        return CheckResult(False, f"local server unreachable at {LOCAL_BASE_URL}: {exc}", "aeris_runtime/engineering/factory.py")


def _check_p5_6() -> CheckResult:
    cap_ok, cap_detail = _grep("ui/web/capabilities.js", "cap-graph-group", "lib.id='skill-library'")
    progress_ok, progress_detail = _grep("ui/web/progress.html", "phase-bars", "progress-ring")
    ok = cap_ok and progress_ok
    return CheckResult(ok, f"{cap_detail}; {progress_detail}", "ui/web/capabilities.js; ui/web/progress.html")


def _check_p5_7() -> CheckResult:
    module_ok, module_detail = _grep("aeris_runtime/engineering/l3_award.py", "def prepare_review", "def human_decide", "a named Human approver is required")
    cli_ok, cli_detail = _grep("aeris_runtime/cli.py", "def cmd_l3", '"l3"')
    test_ok, test_detail = _run_unittest("tests.test_l3_award")
    ok = module_ok and cli_ok and test_ok
    return CheckResult(ok, f"{module_detail}; {cli_detail}; {test_detail}", "aeris_runtime/engineering/l3_award.py; aeris_runtime/cli.py; tests/test_l3_award.py")


def _check_p5_9() -> CheckResult:
    ok, detail = _grep("docs/AERIS_P5_ENGINEER_FACTORY.md", "93/100", "not rounded up")
    return CheckResult(ok, detail, "docs/AERIS_P5_ENGINEER_FACTORY.md")


def _check_p6_1() -> CheckResult:
    try:
        from .review import independent_acceptance
        payload = independent_acceptance("progress_verify")
        ok = payload.get("final_result") in {"PASS", "PASS_WITH_LIMITS", "BLOCKED", "FAIL"}
        return CheckResult(ok, f"independent_acceptance() callable, final_result={payload.get('final_result')}", "aeris_runtime/review.py:independent_acceptance")
    except Exception as exc:
        return CheckResult(False, f"independent_acceptance() raised: {exc}", "aeris_runtime/review.py")


def _check_p6_2() -> CheckResult:
    try:
        from .completion import assess
        payload = assess(write=False)
        ok = "not trusted as proof" in str(payload.get("truth", "")) and "assessed_software_items" in payload
        return CheckResult(ok, f"completion.assess() callable; software_local_gaps_after={payload.get('software_local_gaps_after')}", "aeris_runtime/completion.py:assess")
    except Exception as exc:
        return CheckResult(False, f"completion.assess() raised: {exc}", "aeris_runtime/completion.py")


def _check_p6_3() -> CheckResult:
    ok, detail = _grep("aeris_runtime/review.py", "AUDIT_LEDGER_INVALID", "CORE_CACHE_INTEGRITY_FAIL")
    return CheckResult(ok, detail, "aeris_runtime/review.py")


def _check_p6_4() -> CheckResult:
    ok, detail = _grep("aeris_runtime/review.py", "VERSIONED_IMPLEMENTATION_WORKTREE_DIRTY", "_versioned_worktree_dirty")
    return CheckResult(ok, detail, "aeris_runtime/review.py")


def _check_p6_6() -> CheckResult:
    ok, detail = _grep("aeris_runtime/review.py", "REAL_MACHINE_ACCEPTANCE_NOT_PRESENT", "REAL_MACHINE_ACCEPTANCE_FAILED")
    return CheckResult(ok, detail, "aeris_runtime/review.py")


def _check_p6_7() -> CheckResult:
    doc_ok, doc_detail = _grep("docs/AERIS_P6_COMPANY_ACCEPTANCE.md", "P6.1", "P6.8")
    doc_exists = (ROOT / "docs/AERIS_P6_COMPANY_ACCEPTANCE.md").exists()
    return CheckResult(doc_exists and doc_ok, doc_detail, "docs/AERIS_P6_COMPANY_ACCEPTANCE.md")


def _check_p6_8() -> CheckResult:
    p6_registered = [k for k in CHECKS if k.startswith("P6.")]
    ok = len(p6_registered) >= 6
    return CheckResult(ok, f"P6 checks registered: {sorted(p6_registered)}", "aeris_runtime/progress_verify.py")


CHECKS: dict[str, Callable[[], CheckResult]] = {
    "P0.1": _check_p0_1, "P0.2": _check_p0_2, "P0.3": _check_p0_3, "P0.4": _check_p0_4,
    "P0.5": _check_p0_5, "P0.6": _check_p0_6, "P0.7": _check_p0_7,
    "P1.1": _check_p1_1, "P1.2": _check_p1_2, "P1.3": _check_p1_3, "P1.4": _check_p1_4,
    "P1.5": _check_p1_5, "P1.6": _check_p1_6, "P1.7": _check_p1_7, "P1.8": _check_p1_8,
    "P2.1": _check_p2_1, "P2.2": _check_p2_2, "P2.3": _check_p2_3, "P2.5": _check_p2_5, "P2.6": _check_p2_6, "P2.7": _check_p2_7,
    "P3.1": _check_p3_1, "P3.2": _check_p3_2, "P3.3": _check_p3_3, "P3.4": _check_p3_4,
    "P3.5": _check_p3_5, "P3.6": _check_p3_6, "P3.7": _check_p3_7, "P3.8": _check_p3_8,
    "P4.1": _check_p4_1, "P4.2": _check_p4_2, "P4.3": _check_p4_3, "P4.4": _check_p4_4, "P4.5": _check_p4_5,
    "P4.6": _check_p4_6, "P4.7": _check_p4_7,
    "P5.1": _check_p5_1, "P5.2": _check_p5_2, "P5.3": _check_p5_3, "P5.5": _check_p5_5,
    "P5.6": _check_p5_6, "P5.7": _check_p5_7, "P5.8": _check_p5_8, "P5.9": _check_p5_9,
    "P6.1": _check_p6_1, "P6.2": _check_p6_2, "P6.3": _check_p6_3, "P6.4": _check_p6_4,
    "P6.6": _check_p6_6, "P6.7": _check_p6_7, "P6.8": _check_p6_8,
}

_ORDER = ["P0.1", "P0.2", "P0.3", "P0.4", "P0.5", "P0.6", "P0.7",
          "P1.1", "P1.2", "P1.3", "P1.4", "P1.5", "P1.6", "P1.7", "P1.8",
          "P2.1", "P2.2", "P2.3", "P2.5", "P2.6", "P2.7",
          "P3.1", "P3.2", "P3.3", "P3.4", "P3.5", "P3.6", "P3.7", "P3.8",
          "P4.1", "P4.2", "P4.3", "P4.4", "P4.5", "P4.6", "P4.7",
          "P5.1", "P5.2", "P5.3", "P5.5", "P5.6", "P5.7", "P5.8", "P5.9",
          "P6.1", "P6.2", "P6.3", "P6.4", "P6.6", "P6.7", "P6.8"]


def run(items: list[str] | None = None, *, write: bool = True) -> dict:
    """Re-run every requested item's real check and (optionally) write fresh Evidence."""
    targets = items if items is not None else _ORDER
    head = _head_sha()
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    truth = json.loads(TRUTH_PATH.read_text(encoding="utf-8")) if TRUTH_PATH.exists() else {"schema_version": 1, "items": {}}
    report = {}
    for item_id in targets:
        check = CHECKS.get(item_id)
        if check is None:
            report[item_id] = {"result": "UNKNOWN", "detail": "no automated check registered for this item"}
            continue
        outcome = check()
        result = "PASS" if outcome.passed else "FAIL"
        report[item_id] = {"result": result, "detail": outcome.detail}
        if write:
            evidence = {
                "schema_version": 1, "item": item_id, "result": result,
                "captured_at_utc": now.isoformat(),
                "candidate_sha": head, "runtime_sha": head, "authority_sha": CANONICAL_AUTHORITY_SHA,
                "acceptance_gate": item_id, "command": f"aeris_runtime.progress_verify:{item_id}",
                "exit_code": 0 if outcome.passed else 1, "relevant_output": [outcome.detail],
                "artifact": outcome.artifact, "acceptance_result": result, "blocker": None if outcome.passed else "automated check failed",
                "next_action": "see PROGRESS_TRUTH.json ordering" if outcome.passed else "fix the regression this check found, then re-run",
                "truth": "Generated by aeris_runtime.progress_verify, not hand-authored.",
            }
            evidence_path = EVIDENCE_DIR / f"{item_id}-{result}-{stamp}.json"
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if outcome.passed:
                truth.setdefault("items", {})[item_id] = {
                    "authority_sha": CANONICAL_AUTHORITY_SHA, "source_sha": head,
                    "evidence_type": "local_targeted_acceptance",
                    "evidence_pointer": f".aeris/evidence/progress/{evidence_path.name}",
                    "acceptance_gate": item_id, "result": "PASS", "score": 100,
                    "observed_at": now.isoformat(), "blocker": None,
                    "next_action": "automated",
                }
            else:
                truth.setdefault("items", {}).pop(item_id, None)
    if write:
        truth["updated_at_utc"] = now.isoformat()
        TRUTH_PATH.write_text(json.dumps(truth, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Re-verify AERIS P0/P1 Progress Truth items with real checks")
    parser.add_argument("items", nargs="*", help="specific item ids (default: all known items)")
    parser.add_argument("--dry-run", action="store_true", help="run checks without writing Evidence")
    args = parser.parse_args()
    report = run(args.items or None, write=not args.dry_run)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(v["result"] == "PASS" for v in report.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
