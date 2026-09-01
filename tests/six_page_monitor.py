"""Bounded continuous HTTP monitor for all AERIS light/dark pages."""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / ".aeris" / "evidence" / "six-page-monitor.json"
ROUTES = (
    "/?theme=dark", "/workspace?theme=dark", "/services?theme=dark",
    "/?theme=light", "/workspace?theme=light", "/services?theme=light",
)


def run(base_url: str, cycles: int, interval: float) -> int:
    failures: list[dict[str, object]] = []
    started = datetime.now(timezone.utc).isoformat()
    checks = 0
    for cycle in range(cycles):
        for route in ROUTES:
            checks += 1
            try:
                with urllib.request.urlopen(base_url.rstrip("/") + route, timeout=5) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    if response.status != 200 or "/assets/aeris-live.js" not in body:
                        failures.append({"cycle": cycle, "route": route, "status": response.status, "reason": "application shell missing"})
            except Exception as exc:
                failures.append({"cycle": cycle, "route": route, "reason": f"{type(exc).__name__}: {exc}"})
        if cycle + 1 < cycles:
            time.sleep(interval)
    payload = {
        "schema_version": 1, "result": "PASS" if not failures else "FAIL",
        "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url, "cycles": cycles, "routes": len(ROUTES), "checks": checks,
        "failures": failures[:100], "failure_count": len(failures),
        "scope": "continuous six-page HTTP 200 and AERIS application-shell availability; browser semantic/visual gates are separate",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 8


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--cycles", type=int, default=60)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    raise SystemExit(run(args.base_url, max(1, args.cycles), max(0.0, args.interval)))
