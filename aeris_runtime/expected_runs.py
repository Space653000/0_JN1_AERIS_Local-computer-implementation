"""Expected-run monitor for AERIS observability.

A process heartbeat is not proof that expected work ran. This registry tracks expected
artifacts/success times and reports bounded health states. Latest outcome is stored
explicitly so correctness does not depend on wall-clock timestamp resolution.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import append_event
from .config import ROOT

REGISTRY_PATH = ROOT / ".aeris" / "health" / "expected_runs.json"
DEFAULTS_PATH = ROOT / "config" / "expected_runs.defaults.json"
VALID_STATES = {"HEALTHY", "DEGRADED", "FAILED", "UNKNOWN", "NO_HEARTBEAT", "STALE", "NOT_CONFIGURED", "BLOCKED"}
_LOCK = threading.RLock()
LOCK_PATH = REGISTRY_PATH.with_suffix(".lock")


@contextmanager
def _process_lock():
    """Serialize read-modify-write across supervisor/watchdog/test processes."""
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic() + 10
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("expected-run registry process lock timed out")
                time.sleep(0.05)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read() -> dict[str, Any]:
    with _LOCK:
        if not REGISTRY_PATH.exists():
            return {"schema_version": 1, "expected_runs": {}}
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))


def _write(data: dict[str, Any]) -> None:
    with _LOCK:
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = REGISTRY_PATH.with_name(f"{REGISTRY_PATH.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            # Windows readers may briefly deny FILE_SHARE_DELETE even though
            # writers hold the process lock. Retry the same atomic replacement;
            # never truncate the registry or turn a persistent denial into PASS.
            for attempt in range(20):
                try:
                    tmp.replace(REGISTRY_PATH)
                    break
                except PermissionError:
                    if attempt == 19:
                        raise
                    time.sleep(0.025)
        finally:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass


def ensure_defaults(*, actor: str = "AERIS", audit_event: bool = True) -> dict[str, Any]:
    """Add missing default expected-run contracts without erasing live history."""
    if not DEFAULTS_PATH.exists():
        return _read()
    defaults = json.loads(DEFAULTS_PATH.read_text(encoding="utf-8-sig"))
    items = defaults.get("expected_runs", [])
    if not isinstance(items, list):
        raise ValueError("expected_runs.defaults.json expected_runs must be a list")
    with _process_lock():
        data = _read()
        runs = data.setdefault("expected_runs", {})
        added: list[str] = []
        for spec in items:
            if not isinstance(spec, dict):
                raise ValueError("expected-run default must be an object")
            name = str(spec.get("name", "")).strip()
            max_age = int(spec.get("max_age_sec", 0) or 0)
            if not name or max_age <= 0:
                raise ValueError("default expected run requires name and positive max_age_sec")
            if name in runs:
                continue
            runs[name] = {
            "name": name,
            "max_age_sec": max_age,
            "artifact_path": spec.get("artifact_path"),
            "scope": str(spec.get("scope", "")).strip(),
            "last_result": None,
            "last_event_at_utc": None,
            "last_success_at_utc": None,
            "last_failure_at_utc": None,
            "last_error": None,
            }
            added.append(name)
        if added:
            _write(data)
        if audit_event:
            append_event("EXPECTED_RUN_DEFAULTS_INITIALIZED", actor, {"added": added})
    return data


def register(name: str, *, max_age_sec: int, artifact_path: str | None = None, actor: str = "AERIS") -> dict[str, Any]:
    name = name.strip()
    if not name or max_age_sec <= 0:
        raise ValueError("name and positive max_age_sec are required")
    with _process_lock():
        data = _read()
        data["expected_runs"][name] = {
        "name": name,
        "max_age_sec": int(max_age_sec),
        "artifact_path": artifact_path,
        "scope": "",
        "last_result": None,
        "last_event_at_utc": None,
        "last_success_at_utc": None,
        "last_failure_at_utc": None,
        "last_error": None,
        }
        _write(data)
    append_event("EXPECTED_RUN_REGISTERED", actor, {"name": name, "max_age_sec": int(max_age_sec), "artifact_path": artifact_path})
    return data["expected_runs"][name]


def mark(
    name: str,
    success: bool,
    *,
    error: str = "",
    actor: str = "AERIS",
    audit_event: bool = True,
) -> dict[str, Any]:
    with _process_lock():
        data = _read()
        item = data["expected_runs"].get(name)
        if not item:
            raise KeyError(name)
        stamp = _now().isoformat()
        item["last_result"] = "SUCCESS" if success else "FAILURE"
        item["last_event_at_utc"] = stamp
        if success:
            item["last_success_at_utc"] = stamp
            item["last_error"] = None
        else:
            item["last_failure_at_utc"] = stamp
            item["last_error"] = error[:2000]
        _write(data)
    if audit_event:
        append_event("EXPECTED_RUN_RESULT", actor, {"name": name, "success": bool(success), "error": error[:500]})
    return assess_one(item)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def assess_one(item: dict[str, Any]) -> dict[str, Any]:
    success = _parse(item.get("last_success_at_utc"))
    failure = _parse(item.get("last_failure_at_utc"))
    last_result = str(item.get("last_result") or "").upper()
    artifact = item.get("artifact_path")
    artifact_exists = None
    if artifact:
        p = Path(str(artifact))
        if not p.is_absolute():
            p = ROOT / p
        artifact_exists = p.exists()

    if last_result == "FAILURE":
        state = "FAILED"
        reason = "latest recorded run failed"
    elif last_result == "SUCCESS":
        if not success:
            state = "UNKNOWN"
            reason = "latest result says success but success timestamp is missing/invalid"
        else:
            age = (_now() - success).total_seconds()
            if age > int(item["max_age_sec"]):
                state = "STALE"
                reason = f"last success age {int(age)}s exceeds {item['max_age_sec']}s"
            elif artifact_exists is False:
                state = "DEGRADED"
                reason = "expected artifact is missing"
            else:
                state = "HEALTHY"
                reason = "fresh successful run and expected artifact condition satisfied"
    elif failure and (not success or failure >= success):
        state = "FAILED"
        reason = "latest recorded run failed (legacy timestamp ordering)"
    elif not success:
        state = "UNKNOWN"
        reason = "no successful run recorded"
    else:
        age = (_now() - success).total_seconds()
        if age > int(item["max_age_sec"]):
            state = "STALE"
            reason = f"last success age {int(age)}s exceeds {item['max_age_sec']}s"
        elif artifact_exists is False:
            state = "DEGRADED"
            reason = "expected artifact is missing"
        else:
            state = "HEALTHY"
            reason = "fresh successful run and expected artifact condition satisfied"
    if state not in VALID_STATES:
        state = "UNKNOWN"
    return {**item, "state": state, "reason": reason, "artifact_exists": artifact_exists}


def assess_all() -> dict[str, Any]:
    data = _read()
    runs = [assess_one(item) for item in data.get("expected_runs", {}).values()]
    if not runs:
        overall = "NOT_CONFIGURED"
    elif any(r["state"] in {"FAILED", "BLOCKED"} for r in runs):
        overall = "FAILED"
    elif any(r["state"] in {"STALE", "DEGRADED", "UNKNOWN"} for r in runs):
        overall = "DEGRADED"
    else:
        overall = "HEALTHY"
    return {"overall": overall, "runs": runs, "scope": "expected-run/artifact freshness; not whole-company engineering correctness"}
