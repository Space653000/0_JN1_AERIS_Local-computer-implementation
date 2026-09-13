"""Evidence-derived P0-P6 progress projection for the local Progress Center."""
from __future__ import annotations
import subprocess
from datetime import datetime, timezone
from .config import ROOT
from .operations import supervisor_status
from .progress_truth import CANONICAL_AUTHORITY_SHA, evaluate_progress, load_contract, load_observations

PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6")

def _head_sha() -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=3).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _next_action(truth_state: str, phase_percent: dict, items: list[dict]) -> dict:
    """Name the actual next unfinished item, instead of a stale fixed string.

    A prior version of this function only ever distinguished "P0 incomplete"
    from "everything after P0", so it kept reporting a leftover P0-era
    message ("等待 Human 批准進入 P1") long after P1-P6 had real, unrelated
    progress. Compute it live from the same per-item states the page renders.

    Returned as a structured {"kind", ...} object rather than a pre-rendered
    Chinese sentence, so the bilingual UI can render it in whichever
    language the viewer picked (see ui/web/progress.js's L() usage) instead
    of an API response baking in one fixed UI language.
    """
    if truth_state == "FAIL_CLOSED":
        return {"kind": "fail_closed"}
    for phase in PHASES:
        if phase_percent.get(phase) == 100:
            continue
        pending = [item["id"] for item in items if item["id"].startswith(phase + ".") and item["state"] != "PASS"]
        if pending:
            return {"kind": "phase_pending", "phase": phase, "pending_ids": pending}
    return {"kind": "complete"}


def current() -> dict:
    """Project only durable Evidence that matches the currently loaded runtime."""
    status = supervisor_status()
    runtime_sha = status.get("implementation_sha") if status.get("reachable") else None
    candidate_sha = _head_sha()
    runtime_aligned = bool(runtime_sha and candidate_sha and runtime_sha == candidate_sha)
    contract = load_contract(ROOT)
    observations = load_observations(ROOT)
    evaluation = evaluate_progress(
        contract,
        observations,
        runtime_sha=runtime_sha if runtime_aligned else None,
        evidence_root=ROOT,
    )
    if not runtime_aligned:
        evaluation = evaluation.__class__("FAIL_CLOSED", None, {}, {}, tuple((*evaluation.errors, "runtime_candidate_mismatch")))

    items = []
    required = contract["required_items"]
    raw_items = observations.get("items") if isinstance(observations.get("items"), dict) else {}
    for phase in PHASES:
        for ident in required[phase]:
            record = raw_items.get(ident) if isinstance(raw_items.get(ident), dict) else {}
            score = evaluation.item_scores.get(ident)
            state = record.get("result", "UNKNOWN") if score is not None and evaluation.state != "FAIL_CLOSED" else "UNKNOWN"
            items.append({
                "id": ident,
                "percent": score or 0,
                "state": state,
                "evidence": record.get("evidence_pointer") if score is not None else None,
                "sha": record.get("source_sha") if score is not None else runtime_sha,
                "blocker": record.get("blocker") if score is not None else None,
                "next_action": record.get("next_action") if score is not None else "建立本項 authoritative Evidence",
                "acceptance_gate": record.get("acceptance_gate") if score is not None else None,
            })

    phase_percent = evaluation.phase_percent if evaluation.state != "FAIL_CLOSED" else {phase: None for phase in PHASES}
    next_action = _next_action(evaluation.state, phase_percent, items)
    return {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "implementation_sha": runtime_sha,
        "candidate_sha": candidate_sha,
        "runtime_candidate_aligned": runtime_aligned,
        "canonical_authority_sha": CANONICAL_AUTHORITY_SHA,
        "overall_percent": evaluation.overall_percent,
        "phase_percent": phase_percent,
        "items": items,
        "blockers": status.get("blockers") or [],
        "next_action": next_action,
        "truth_state": evaluation.state,
        "truth_errors": list(evaluation.errors),
        "truth": "Evidence-only projection. Missing Evidence is UNKNOWN; mismatched runtime/candidate or invalid Evidence fails closed.",
    }
