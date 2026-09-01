"""AERIS engineering task identity + guarded state transitions."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import append_event
from .config import ROOT

TASK_ROOT = ROOT / ".aeris" / "tasks"

PRIMARY_STATES = ["DRAFT", "READY", "EXECUTING", "EXECUTED", "EVIDENCED", "VERIFIED", "APPROVED", "RELEASED"]
FAILURE_STATES = ["FAILED_EXECUTION", "FAILED_EVIDENCE", "FAILED_VERIFICATION", "REJECTED", "STALE", "BLOCKED", "CANCELLED"]
ALL_STATES = set(PRIMARY_STATES + FAILURE_STATES)

ALLOWED: dict[str, set[str]] = {
    "DRAFT": {"READY", "BLOCKED", "CANCELLED"},
    "READY": {"EXECUTING", "BLOCKED", "CANCELLED"},
    "EXECUTING": {"EXECUTED", "FAILED_EXECUTION", "BLOCKED", "CANCELLED"},
    "EXECUTED": {"EVIDENCED", "FAILED_EVIDENCE", "BLOCKED", "CANCELLED"},
    "EVIDENCED": {"VERIFIED", "FAILED_VERIFICATION", "REJECTED", "STALE", "BLOCKED"},
    "VERIFIED": {"APPROVED", "REJECTED", "STALE", "BLOCKED"},
    "APPROVED": {"RELEASED", "REJECTED", "STALE", "BLOCKED"},
    "RELEASED": {"STALE"},
    "FAILED_EXECUTION": {"READY", "CANCELLED"},
    "FAILED_EVIDENCE": {"EXECUTED", "READY", "CANCELLED"},
    "FAILED_VERIFICATION": {"EVIDENCED", "READY", "CANCELLED"},
    "REJECTED": {"DRAFT", "CANCELLED"},
    "STALE": {"READY", "DRAFT", "CANCELLED"},
    "BLOCKED": {"READY", "DRAFT", "CANCELLED"},
    "CANCELLED": set(),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "-", value.strip())
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("invalid task_id")
    return cleaned[:120]


def task_path(task_id: str) -> Path:
    return TASK_ROOT / _safe_id(task_id) / "task.json"


def create_task(summary: str, actor: str, *, task_id: str | None = None, risk: str = "R0", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if not summary.strip() or not actor.strip():
        raise ValueError("summary and actor are required")
    task_id = _safe_id(task_id or f"AERIS-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}")
    path = task_path(task_id)
    if path.exists():
        raise FileExistsError(f"task already exists: {task_id}")
    path.parent.mkdir(parents=True, exist_ok=False)
    task = {
        "schema_version": 1,
        "task_id": task_id,
        "summary": summary.strip(),
        "risk": risk.strip().upper(),
        "state": "DRAFT",
        "created_by": actor.strip(),
        "created_at_utc": _now(),
        "updated_at_utc": _now(),
        "metadata": metadata or {},
        "history": [{"from": None, "to": "DRAFT", "actor": actor.strip(), "at_utc": _now(), "evidence_refs": []}],
    }
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_event("TASK_CREATED", actor, {"task_id": task_id, "summary": summary, "risk": task["risk"]})
    return task


def load_task(task_id: str) -> dict[str, Any]:
    path = task_path(task_id)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def transition_task(
    task_id: str,
    new_state: str,
    actor: str,
    *,
    evidence_refs: list[str] | None = None,
    note: str = "",
    authority: str = "",
) -> dict[str, Any]:
    new_state = new_state.strip().upper()
    if new_state not in ALL_STATES:
        raise ValueError(f"unsupported state: {new_state}")
    task = load_task(task_id)
    current = str(task.get("state", ""))
    if new_state not in ALLOWED.get(current, set()):
        raise ValueError(f"forbidden AERIS task transition: {current} -> {new_state}")
    refs = [str(item) for item in (evidence_refs or []) if str(item).strip()]
    if new_state in {"EVIDENCED", "VERIFIED", "APPROVED", "RELEASED"} and not refs:
        raise ValueError(f"{new_state} requires at least one evidence reference")
    if new_state == "VERIFIED" and not authority:
        raise ValueError("VERIFIED requires reviewer/verification authority")
    if new_state == "APPROVED" and authority != "Human Chief Engineer":
        raise ValueError("APPROVED requires authority='Human Chief Engineer'")
    if new_state == "RELEASED" and authority != "Human Chief Engineer":
        raise ValueError("RELEASED requires Human Chief Engineer authority")

    event = {
        "from": current,
        "to": new_state,
        "actor": actor.strip(),
        "authority": authority,
        "at_utc": _now(),
        "evidence_refs": refs,
        "note": note.strip(),
    }
    task["state"] = new_state
    task["updated_at_utc"] = event["at_utc"]
    task.setdefault("history", []).append(event)
    path = task_path(task_id)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    append_event("TASK_TRANSITION", actor, {"task_id": task_id, **event})
    return task


def validate_task(task: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if task.get("state") not in ALL_STATES:
        errors.append("unknown state")
    history = task.get("history", [])
    if not history or history[0].get("to") != "DRAFT":
        errors.append("history must begin at DRAFT")
    previous = None
    for index, event in enumerate(history):
        target = event.get("to")
        source = event.get("from")
        if index == 0:
            previous = target
            continue
        if source != previous:
            errors.append(f"history {index}: source does not match previous state")
        if target not in ALLOWED.get(str(source), set()):
            errors.append(f"history {index}: forbidden transition {source}->{target}")
        previous = target
    if history and task.get("state") != history[-1].get("to"):
        errors.append("current state does not match history tail")
    return errors
