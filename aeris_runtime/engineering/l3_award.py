"""L3 role-domain award: AI prepares/organizes the review; only a Human grants it.

Every existing `role_l3_awarded: False` self-report inside domain_review.py
and challenges.py stays exactly as it is -- those remain honest, fail-closed
AI self-assessments and this module never mutates them. This module adds a
second, separate, hash-chained ledger (reusing aeris_runtime.audit's
primitive) whose only writers are:

  1. prepare_review() -- AI packages an already-completed, independently
     reviewed and replayed challenges.run() receipt into a compact packet for
     Human consideration. It computes no new judgment; it organizes an
     existing one.
  2. human_decide() -- the *only* place a role/skill can ever be marked
     L3-awarded. It requires a named Human approver and a GRANT/REJECT
     decision, and must only ever be invoked by a Human action (the CLI
     `aeris l3 award` command, or an explicit dashboard control) -- never
     from an autonomous code path.

role_l3_status() re-verifies the underlying challenge evidence on every call
(fail-closed): a GRANT whose backing evidence no longer validates is silently
excluded rather than trusted from the ledger alone.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import audit
from ..config import ROOT
from . import challenges

LEDGER_DIR = ROOT / ".aeris" / "l3_awards"
LEDGER_PATH = LEDGER_DIR / "ledger.jsonl"

_PREPARED = "L3_REVIEW_PREPARED"
_GRANTED = "L3_AWARD_GRANTED"
_REJECTED = "L3_AWARD_REJECTED"
_REVOKED = "L3_AWARD_REVOKED"
_DECIDED = (_GRANTED, _REJECTED)


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _packet_sha256(packet: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(packet)).hexdigest()


def _ledger_records() -> list[dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    records = []
    with LEDGER_PATH.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def prepare_review(run_id: str) -> dict[str, Any]:
    """AI organizes an already-sealed challenge receipt into a Human review packet.

    Raises ValueError if the referenced challenge run does not currently
    re-verify -- a packet can never be prepared from a claim that does not
    presently hold.
    """
    verified = challenges.status(run_id)
    if not verified.get("valid"):
        raise ValueError("challenge run does not currently re-verify: " + verified.get("reason", ""))
    from .. import evidence
    from . import factory

    record = factory.read(evidence.bundle_dir(run_id) / "processed/challenge.json")
    ai_summary = {
        "result": record["result"],
        "challenge_id": record["challenge_id"],
        "stage_decisions": [stage["report"]["review"]["decision"] for stage in record["stages"]],
        "capability_gaps_before": record["capability_gaps_before"],
        "role_l3_awarded_self_report": record["role_l3_awarded"],
        "human_approval_self_report": record["human_approval"],
    }
    if ai_summary["role_l3_awarded_self_report"] is not False or ai_summary["human_approval_self_report"] is not False:
        raise ValueError("challenge self-report is not the expected unawarded baseline")
    packet = {
        "role_id": record["role_id"],
        "skill_id": record["skill_id"],
        "challenge_id": record["challenge_id"],
        "execution_run_id": run_id,
        "ai_summary": ai_summary,
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    packet_sha256 = _packet_sha256(packet)
    entry = audit.append_event(_PREPARED, "AERIS_AI", {**packet, "packet_sha256": packet_sha256}, path=LEDGER_PATH)
    return {**packet, "packet_sha256": packet_sha256, "event_id": entry["event_id"]}


def pending_review_packets() -> list[dict[str, Any]]:
    """Prepared packets awaiting a Human GRANT or REJECT decision."""
    prepared: dict[str, dict[str, Any]] = {}
    decided: set[str] = set()
    for record in _ledger_records():
        if record["event_type"] == _PREPARED:
            prepared[record["payload"]["packet_sha256"]] = record["payload"]
        elif record["event_type"] in _DECIDED:
            decided.add(record["payload"]["packet_sha256"])
    return [packet for sha, packet in prepared.items() if sha not in decided]


def human_decide(packet_sha256: str, approver: str, decision: str, note: str = "") -> dict[str, Any]:
    """The sole place a role/skill can ever become L3-awarded: an explicit Human act.

    Must only ever be called from a Human-initiated path (CLI command or an
    explicit dashboard Approve/Reject control) -- never automatically.
    """
    if decision not in ("GRANT", "REJECT"):
        raise ValueError("decision must be 'GRANT' or 'REJECT'")
    if not approver or not approver.strip():
        raise ValueError("a named Human approver is required")
    pending = {packet["packet_sha256"]: packet for packet in pending_review_packets()}
    if packet_sha256 not in pending:
        raise ValueError("unknown or already-decided review packet")
    packet = pending[packet_sha256]
    event_type = _GRANTED if decision == "GRANT" else _REJECTED
    return audit.append_event(event_type, approver.strip(), {
        "packet_sha256": packet_sha256, "role_id": packet["role_id"], "skill_id": packet["skill_id"],
        "challenge_id": packet["challenge_id"], "execution_run_id": packet["execution_run_id"], "note": note,
    }, path=LEDGER_PATH)


def human_revoke(packet_sha256: str, approver: str, note: str = "") -> dict[str, Any]:
    """A Human may revoke a prior GRANT (e.g. once new evidence undermines it)."""
    if not approver or not approver.strip():
        raise ValueError("a named Human approver is required")
    granted = {record["payload"]["packet_sha256"]: record["payload"] for record in _ledger_records()
               if record["event_type"] == _GRANTED}
    revoked = {record["payload"]["packet_sha256"] for record in _ledger_records() if record["event_type"] == _REVOKED}
    if packet_sha256 not in granted or packet_sha256 in revoked:
        raise ValueError("no active grant for this review packet")
    payload = granted[packet_sha256]
    return audit.append_event(_REVOKED, approver.strip(), {**payload, "note": note}, path=LEDGER_PATH)


def role_l3_status(role_id: str, skill_id: str | None = None) -> dict[str, Any]:
    """Currently active L3 grants for a role, re-verifying the backing evidence every call."""
    granted: dict[str, dict[str, Any]] = {}
    revoked: set[str] = set()
    for record in _ledger_records():
        if record["event_type"] == _GRANTED:
            payload = record["payload"]
            if payload["role_id"] == role_id:
                granted[payload["skill_id"]] = payload
        elif record["event_type"] == _REVOKED:
            revoked.add(record["payload"]["packet_sha256"])
    active = []
    for skill, payload in granted.items():
        if skill_id and skill != skill_id:
            continue
        if payload["packet_sha256"] in revoked:
            continue
        if not challenges.status(payload["execution_run_id"]).get("valid"):
            continue
        active.append({"skill_id": skill, "execution_run_id": payload["execution_run_id"],
                        "packet_sha256": payload["packet_sha256"]})
    return {"role_id": role_id, "l3_awarded_skills": sorted(item["skill_id"] for item in active), "grants": active}


def verify_ledger() -> dict[str, Any]:
    return audit.verify_ledger(path=LEDGER_PATH)
