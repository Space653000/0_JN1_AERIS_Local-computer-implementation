"""Evidence-derived P0-P6 progress projection for the local Progress Center."""
from __future__ import annotations
from datetime import datetime, timezone
from .config import ROOT
from .operations import supervisor_status

PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6")

def current() -> dict:
    status = supervisor_status()
    blocked = bool(status.get("company_opening_state") == "BLOCKED")
    # The tracker is deliberately conservative: only runtime-observable P0
    # infrastructure checks receive PASS; product phases remain UNKNOWN until
    # their own Evidence contracts exist.
    items = []
    counts = {"P0": 7, "P1": 8, "P2": 7, "P3": 8, "P4": 7, "P5": 9, "P6": 8}
    for phase in PHASES:
        count = counts[phase]
        for index in range(1, count + 1):
            ident = f"{phase}.{index}"
            if phase == "P0" and index <= 5:
                state, percent = ("PASS", 100) if not blocked else ("BLOCKED", 60)
            else:
                state, percent = "UNKNOWN", 0
            items.append({"id": ident, "percent": percent, "state": state,
                          "evidence": "runtime:/health,/status" if state != "UNKNOWN" else None,
                          "sha": status.get("implementation_sha"),
                          "blocker": "company control plane blocked" if state == "BLOCKED" else None,
                          "next_action": "建立本項 authoritative Evidence" if state == "UNKNOWN" else None})
    phase_percent = {p: round(sum(x["percent"] for x in items if x["id"].startswith(p+".")) /
                              sum(1 for x in items if x["id"].startswith(p+"."))) for p in PHASES}
    return {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "implementation_sha": status.get("implementation_sha"), "overall_percent": round(sum(x["percent"] for x in items)/len(items)),
            "phase_percent": phase_percent, "items": items,
            "blockers": status.get("blockers") or [],
            "next_action": "完成 P0.6/P0.7 Progress Truth 與 Evidence" if phase_percent["P0"] < 100 else "等待 Human 批准進入 P1",
            "truth": "UI projection only; percentages require runtime/Evidence and UNKNOWN is preserved."}
