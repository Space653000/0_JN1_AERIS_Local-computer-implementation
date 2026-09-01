"""AERIS unattended local-operations watchdog.

Keeps the loopback control plane available after normal crashes. It never weakens
opening, Core, privacy, model, or Human gates: if the supervisor cannot start because
those gates block, the watchdog records BLOCKED instead of bypassing them.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .audit import append_event
from .config import ROOT
from .operations import DEFAULT_PORT, start_supervisor_background, supervisor_status

STATE_FILE = ROOT / ".aeris" / "state" / "UNATTENDED_OPERATIONS.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(payload: dict[str, Any]) -> dict[str, Any]:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)
    return payload


def reconcile_once(
    port: int = DEFAULT_PORT,
    *,
    status_fn: Callable[..., dict[str, Any]] = supervisor_status,
    start_fn: Callable[..., dict[str, Any]] = start_supervisor_background,
) -> dict[str, Any]:
    before = status_fn(port)
    if before.get("reachable"):
        return _write({
            "schema_version": 1,
            "assessed_at_utc": _now(),
            "watchdog_pid": os.getpid(),
            "state": "HEALTHY",
            "action": "NONE_ALREADY_SERVING",
            "supervisor": before,
            "truth": "Watchdog health proves loopback service continuity only, not whole-company engineering correctness.",
        })

    attempt = start_fn(port)
    after = status_fn(port)
    if after.get("reachable"):
        state, action = "RECOVERED", "SUPERVISOR_RESTARTED"
        append_event("UNATTENDED_SUPERVISOR_RECOVERED", "AERIS Watchdog", {"port": int(port), "attempt": attempt})
    else:
        state, action = "BLOCKED_OR_FAILED", "RESTART_FAILED_NO_GATE_BYPASS"
        append_event("UNATTENDED_SUPERVISOR_RECOVERY_FAILED", "AERIS Watchdog", {"port": int(port), "attempt": attempt, "after": after})
    return _write({
        "schema_version": 1,
        "assessed_at_utc": _now(),
        "watchdog_pid": os.getpid(),
        "state": state,
        "action": action,
        "before": before,
        "start_attempt": attempt,
        "supervisor": after,
        "truth": "A failed restart is recorded; watchdog never bypasses Core/privacy/acceptance/Human gates.",
    })


def run_forever(port: int = DEFAULT_PORT, interval_sec: int = 20) -> int:
    interval_sec = max(5, min(int(interval_sec), 3600))
    append_event("UNATTENDED_WATCHDOG_STARTED", "AERIS Watchdog", {"pid": os.getpid(), "port": int(port), "interval_sec": interval_sec})
    consecutive_errors = 0
    while True:
        try:
            reconcile_once(port)
            consecutive_errors = 0
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            append_event("UNATTENDED_WATCHDOG_STOPPED", "AERIS Watchdog", {"pid": os.getpid(), "reason": "keyboard_interrupt"})
            return 0
        except Exception as exc:
            consecutive_errors += 1
            _write({
                "schema_version": 1,
                "assessed_at_utc": _now(),
                "watchdog_pid": os.getpid(),
                "state": "DEGRADED",
                "action": "WATCHDOG_LOOP_EXCEPTION_RETRYING",
                "error_type": type(exc).__name__,
                "error": str(exc)[:2000],
                "consecutive_errors": consecutive_errors,
            })
            # Stay alive so OS persistence is not the only recovery layer.
            time.sleep(min(300, max(interval_sec, 5 * consecutive_errors)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AERIS unattended local-operations watchdog")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--interval", type=int, default=20)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    if args.once:
        report = reconcile_once(args.port)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("state") in {"HEALTHY", "RECOVERED"} else 8
    return run_forever(args.port, args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
