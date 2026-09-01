"""AERIS G0-G5 verification record baseline."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import append_event
from .config import ROOT
from .taskstate import load_task

VERIFICATION_ROOT = ROOT / ".aeris" / "verification"
GATES = ["G0_CONTRACT", "G1_NUMERICAL", "G2_DOMAIN", "G3_REGRESSION", "G4_INDEPENDENT_REVIEW", "G5_APPROVAL"]
OUTCOMES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}


def record_path(task_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in task_id)
    return VERIFICATION_ROOT / safe / "gates.json"


def load_gates(task_id: str) -> dict[str, Any]:
    path = record_path(task_id)
    if not path.exists():
        return {
            "schema_version": 1,
            "task_id": task_id,
            "gates": {gate: {"outcome": "NOT_RUN"} for gate in GATES},
            "scope": "structured_gate_records_baseline_not_full_domain_verification_engine",
        }
    return json.loads(path.read_text(encoding="utf-8-sig"))


def record_gate(
    task_id: str,
    gate: str,
    outcome: str,
    reviewer: str,
    *,
    evidence_refs: list[str] | None = None,
    note: str = "",
    reviewer_role: str = "",
) -> dict[str, Any]:
    gate = gate.strip().upper()
    outcome = outcome.strip().upper()
    if gate not in GATES:
        raise ValueError(f"unsupported gate: {gate}")
    if outcome not in OUTCOMES - {"NOT_RUN"}:
        raise ValueError(f"unsupported gate outcome: {outcome}")
    task = load_task(task_id)
    refs = [str(x) for x in (evidence_refs or []) if str(x).strip()]
    if outcome == "PASS" and not refs:
        raise ValueError("PASS requires at least one evidence reference")
    if gate == "G4_INDEPENDENT_REVIEW" and outcome == "PASS":
        if reviewer.strip() == str(task.get("created_by", "")).strip():
            raise ValueError("G4 independent reviewer cannot be the task creator/executor identity")
        if reviewer_role != "independent_reviewer":
            raise ValueError("G4 PASS requires reviewer_role='independent_reviewer'")
    if gate == "G5_APPROVAL" and outcome == "PASS" and reviewer_role != "Human Chief Engineer":
        raise ValueError("G5 PASS requires reviewer_role='Human Chief Engineer'")

    state = load_gates(task_id)
    entry = {
        "outcome": outcome,
        "reviewer": reviewer.strip(),
        "reviewer_role": reviewer_role,
        "evidence_refs": refs,
        "note": note.strip(),
        "at_utc": datetime.now(timezone.utc).isoformat(),
    }
    state["gates"][gate] = entry
    path = record_path(task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    append_event("VERIFICATION_GATE_RECORDED", reviewer, {"task_id": task_id, "gate": gate, **entry})
    return state


def gate_summary(task_id: str) -> dict[str, Any]:
    state = load_gates(task_id)
    outcomes = {gate: state["gates"].get(gate, {}).get("outcome", "NOT_RUN") for gate in GATES}
    return {
        "task_id": task_id,
        "outcomes": outcomes,
        "g0_g4_passed": all(outcomes[g] == "PASS" for g in GATES[:5]),
        "all_g0_g5_passed": all(outcomes[g] == "PASS" for g in GATES),
        "scope": state.get("scope"),
    }
