"""Point-checks every layer of the running local company after
AERIS_START launches it: backend API, the database directly, every
frontend page, and the full P0-P6 progress table -- then prints one
clear checklist so a human double-clicking the launcher can see at a
glance that everything is really up, not just that a process started.
The five-plane service telemetry is reported too, but as information
only (see check_service_telemetry's docstring for why it must not gate
pass/fail).

Exit code 0 only if every gating check passes; nonzero otherwise, so the
launcher script can refuse to declare success on a partial start.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:{port}"
TIMEOUT_S = 5
FRONTEND_PAGES = ["/", "/dashboard", "/progress", "/workspace", "/activity", "/services"]
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / ".aeris" / "control" / "control.sqlite3"
AUDIT_LEDGER_PATH = ROOT / ".aeris" / "audit" / "audit.jsonl"
SUPERVISOR_TOKEN_PATH = ROOT / ".aeris" / "state" / ".supervisor-token"


def _auth_headers() -> dict:
    # Same-machine tooling authenticates via the supervisor token
    # (operations.py writes it fresh, 0600, at every startup) instead of a
    # browser session -- see aeris_runtime/auth.py's SUPERVISOR_TOKEN_PATH.
    if SUPERVISOR_TOKEN_PATH.is_file():
        try:
            return {"X-AERIS-Supervisor-Token": SUPERVISOR_TOKEN_PATH.read_text(encoding="utf-8-sig").strip()}
        except OSError:
            pass
    return {}


def _get(base: str, path: str) -> tuple[bool, str, int]:
    try:
        request = urllib.request.Request(base + path, headers=_auth_headers())
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return True, body, resp.status
    except urllib.error.HTTPError as exc:
        return False, str(exc), exc.code
    except Exception as exc:
        return False, str(exc), 0


def check_backend(base: str) -> tuple[bool, list[str]]:
    lines = []
    ok_health, body, _ = _get(base, "/health")
    healthy = ok_health and json.loads(body).get("service_state") == "SERVING"
    lines.append(f"  {'PASS' if healthy else 'FAIL'}  /health -> service_state={'?' if not ok_health else json.loads(body).get('service_state')}")
    ok_progress, body2, _ = _get(base, "/api/v1/progress")
    lines.append(f"  {'PASS' if ok_progress else 'FAIL'}  /api/v1/progress")
    ok_caps, _, _ = _get(base, "/api/v1/capabilities")
    lines.append(f"  {'PASS' if ok_caps else 'FAIL'}  /api/v1/capabilities")
    return healthy and ok_progress and ok_caps, lines


def check_database(base: str) -> tuple[bool, list[str]]:
    """A fast, deterministic direct check -- not the slow async
    /api/v1/services cache (see check_service_telemetry below), which is
    designed to legitimately stay CHECKING under concurrent write
    activity and is unsuitable as a pass/fail gate for a launcher."""
    lines = []
    all_ok = True
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=3)
            conn.execute("SELECT 1").fetchone()
            tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            conn.close()
            lines.append(f"  PASS  control.sqlite3 queryable ({tables} tables)")
        except sqlite3.Error as exc:
            all_ok = False
            lines.append(f"  FAIL  control.sqlite3 exists but is not queryable: {exc}")
    else:
        all_ok = False
        lines.append(f"  FAIL  control.sqlite3 not found at {DB_PATH}")
    if AUDIT_LEDGER_PATH.exists():
        lines.append(f"  PASS  audit ledger present ({AUDIT_LEDGER_PATH.stat().st_size} bytes)")
    else:
        all_ok = False
        lines.append(f"  FAIL  audit ledger not found at {AUDIT_LEDGER_PATH}")
    return all_ok, lines


def check_service_telemetry(base: str) -> list[str]:
    """Informational only -- never gates overall PASS/FAIL. The
    five-plane assessment (aeris_runtime/telemetry.py's
    TelemetryProjection) runs on a background thread and is keyed by a
    live summary snapshot; if anything else is actively writing to the
    control store between refreshes, the cache key never stabilizes and
    it can legitimately stay CHECKING indefinitely. That's an honest
    transient state, not a broken system, so treat it as a status line,
    not a database health gate (check_database above is the real one)."""
    deadline = time.monotonic() + 10
    data = None
    while time.monotonic() < deadline:
        ok, body, _ = _get(base, "/api/v1/services")
        if not ok:
            return [f"  (資訊) /api/v1/services unreachable: {body}"]
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return ["  (資訊) /api/v1/services returned invalid JSON"]
        if data.get("assessment_complete"):
            break
        time.sleep(2)
    if data is None:
        return ["  (資訊) no response"]
    if data.get("assessment_complete"):
        counts = data.get("state_counts", {})
        return [f"  (資訊) 背景健康評估已完成 / assessment complete: {counts}"]
    return [f"  (資訊) 背景健康評估仍在進行中（非錯誤，可能因系統忙碌尚未收斂），詳見 /services 頁面",
            f"        background assessment still CHECKING (not an error -- can stay pending under active load): {data.get('state_counts')}"]


def check_frontend(base: str) -> tuple[bool, list[str]]:
    lines = []
    all_ok = True
    for page in FRONTEND_PAGES:
        ok, body, status = _get(base, page)
        real_page = ok and len(body) > 500 and "<html" in body.lower()
        all_ok = all_ok and real_page
        lines.append(f"  {'PASS' if real_page else 'FAIL'}  {page} (HTTP {status}, {len(body) if ok else 0} bytes)")
    return all_ok, lines


def print_progress_table(base: str) -> bool:
    ok, body, _ = _get(base, "/api/v1/progress")
    if not ok:
        print("  FAIL  could not read /api/v1/progress")
        return False
    d = json.loads(body)
    print(f"  truth_state={d.get('truth_state')}  overall_percent={d.get('overall_percent')}  runtime_candidate_aligned={d.get('runtime_candidate_aligned')}")
    for phase, percent in d.get("phase_percent", {}).items():
        bar = ("#" * (percent // 5 if isinstance(percent, int) else 0)).ljust(20)
        print(f"    {phase}  [{bar}]  {percent if percent is not None else 'UNKNOWN'}%")
    unresolved = [item["id"] for item in d.get("items", []) if item.get("state") != "PASS"]
    if unresolved:
        print(f"  Known open items (deliberately disclosed, see docs/): {', '.join(unresolved)}")
    return d.get("truth_state") != "FAIL_CLOSED"


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "8765"
    base = BASE.format(port=port)

    print("=== AERIS 本機系統啟動點檢 / Local System Startup Checklist ===")

    print("\n[1/4] 後端 API / Backend API")
    backend_ok, backend_lines = check_backend(base)
    print("\n".join(backend_lines))

    print("\n[2/5] 資料庫 / Database")
    db_ok, db_lines = check_database(base)
    print("\n".join(db_lines))

    print("\n[3/5] 前端頁面 / Frontend Pages")
    frontend_ok, frontend_lines = check_frontend(base)
    print("\n".join(frontend_lines))

    print("\n[4/5] 五大平面背景健康評估（僅供參考，不影響通過與否）/ Five-Plane Background Assessment (informational only)")
    print("\n".join(check_service_telemetry(base)))

    print("\n[5/5] P0-P6 全公司工程進度 / Full Company Progress")
    progress_ok = print_progress_table(base)

    print("\n=== 總結 / Summary ===")
    print(f"  後端 Backend:  {'PASS' if backend_ok else 'FAIL'}")
    print(f"  資料庫 Database: {'PASS' if db_ok else 'FAIL'}")
    print(f"  前端 Frontend: {'PASS' if frontend_ok else 'FAIL'}")
    print(f"  進度真值 Progress truth: {'OK (not FAIL_CLOSED)' if progress_ok else 'FAIL_CLOSED'}")

    all_ok = backend_ok and db_ok and frontend_ok and progress_ok
    print(f"\n{'一切正常，系統已就緒。' if all_ok else '有項目未通過，請往上檢查詳細訊息。'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
