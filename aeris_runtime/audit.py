"""Hash-chained local audit ledger for AERIS trust primitives.

This is an application-level append-only baseline. It detects ordinary record
modification/removal/reordering relative to the chain, but it is not WORM
storage or a cryptographic external attestation service.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import ROOT

AUDIT_DIR = ROOT / ".aeris" / "audit"
AUDIT_FILE = AUDIT_DIR / "audit.jsonl"
LOCK_FILE = AUDIT_DIR / ".audit.lock"


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash_record(record_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(record_without_hash)).hexdigest()


@contextmanager
def _single_writer_lock(timeout_sec: float = 5.0) -> Iterator[None]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_sec
    fd: int | None = None
    while fd is None:
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, f"pid={os.getpid()}\n".encode())
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError("AERIS audit ledger single-writer lock timed out")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            if fd is not None:
                os.close(fd)
        finally:
            try:
                LOCK_FILE.unlink()
            except FileNotFoundError:
                pass


def _last_hash(path: Path = AUDIT_FILE) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return "0" * 64
    last = ""
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                last = line
    if not last:
        return "0" * 64
    return str(json.loads(last).get("record_hash", ""))


def append_event(event_type: str, actor: str, payload: dict[str, Any] | None = None, *, path: Path = AUDIT_FILE) -> dict[str, Any]:
    """Append one hash-chained event and return the stored record."""
    if not event_type.strip() or not actor.strip():
        raise ValueError("event_type and actor are required")
    path.parent.mkdir(parents=True, exist_ok=True)
    with _single_writer_lock():
        record: dict[str, Any] = {
            "schema_version": 1,
            "event_id": str(uuid.uuid4()),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.strip(),
            "actor": actor.strip(),
            "payload": payload or {},
            "prev_hash": _last_hash(path),
        }
        record["record_hash"] = _hash_record(record)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        return record


def verify_ledger(path: Path = AUDIT_FILE) -> dict[str, Any]:
    if not path.exists():
        return {"valid": True, "records": 0, "last_hash": "0" * 64, "note": "ledger_not_created_yet"}
    expected_prev = "0" * 64
    count = 0
    errors: list[str] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"line {number}: invalid JSON: {exc}")
                continue
            actual_hash = str(record.get("record_hash", ""))
            base = dict(record)
            base.pop("record_hash", None)
            calculated = _hash_record(base)
            if record.get("prev_hash") != expected_prev:
                errors.append(f"line {number}: prev_hash chain mismatch")
            if actual_hash != calculated:
                errors.append(f"line {number}: record_hash mismatch")
            expected_prev = actual_hash
            count += 1
    return {
        "valid": not errors,
        "records": count,
        "last_hash": expected_prev,
        "errors": errors,
        "scope": "application_hash_chain_not_worm_or_external_attestation",
    }
