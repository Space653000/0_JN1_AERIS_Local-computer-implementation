"""Deterministic completion-pass and remaining-gate inventory."""
from __future__ import annotations

import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ROOT

PASS = ROOT / "config" / "completion_pass.v1.json"
MATURITY = ROOT / "config" / "maturity.json"
REPORT = ROOT / ".aeris" / "state" / "SOFTWARE_COMPLETION.json"
GATE_STATES = {"HUMAN_GATE", "EXTERNAL_LICENSE", "PHYSICAL_HARDWARE", "REBOOT_LOGOFF_REQUIRED"}


def assess(write: bool = False) -> dict[str, Any]:
    spec = json.loads(PASS.read_text(encoding="utf-8-sig"))
    maturity = json.loads(MATURITY.read_text(encoding="utf-8-sig"))
    unresolved = [item for item in spec["items"] if item["classification"] == "SOFTWARE_LOCAL_FIXABLE" and item["status"] != "COMPLETE"]
    gates = [{"capability": name, "classification": item["state"], "required": item.get("required", "")} for name, item in maturity["capabilities"].items() if item.get("state") in GATE_STATES]
    payload = {
        "schema_version": 1, "assessed_at_utc": datetime.now(timezone.utc).isoformat(),
        "software_local_gaps_before": int(spec["software_local_gaps_before"]),
        "software_local_gaps_after": len(unresolved), "software_local_fixable_zero": not unresolved,
        "unresolved_software_gaps": unresolved, "remaining_external_blockers": gates,
        "remote_write_performed": False, "local_only_scope": True,
        "truth": spec["truth"],
    }
    if write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        tmp = REPORT.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(REPORT)
    return payload


def main() -> int:
    parser=argparse.ArgumentParser(description="Assess AERIS software-local completion")
    parser.add_argument("--write", action="store_true")
    args=parser.parse_args()
    payload=assess(write=args.write)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["software_local_fixable_zero"] else 8


if __name__ == "__main__":
    raise SystemExit(main())
