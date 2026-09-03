"""AERIS local company opening state and loopback-only supervisor."""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .audit import append_event, verify_ledger
from .company import validate_company_manifest
from .config import ROOT, load_config
from .controlplane import handle_get as controlplane_get, handle_post as controlplane_post
from .corecache import verify_core_cache
from .expected_runs import ensure_defaults as ensure_expected_runs, mark as mark_expected_run
from .machine import detect as machine_detect
from .router import ModelRouter

STATE_DIR = ROOT / ".aeris" / "state"
OPENING_FILE = STATE_DIR / "COMPANY_OPENING.json"
HEARTBEAT_FILE = STATE_DIR / "HEARTBEAT.json"
SUPERVISOR_FILE = STATE_DIR / "SUPERVISOR.json"
SUPERVISOR_TOKEN_FILE = STATE_DIR / ".supervisor-token"
ACCEPTANCE_FILE = STATE_DIR / "LOCAL_ACCEPTANCE.json"
MATURITY_FILE = ROOT / "config" / "maturity.json"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _loaded_revision() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=5).strip()
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"


# Capture once at module load; a later git commit must not relabel old code.
LOADED_IMPLEMENTATION_SHA = _loaded_revision()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _unverified_capabilities() -> list[dict[str, str]]:
    maturity = _read_json(MATURITY_FILE) or {}
    result: list[dict[str, str]] = []
    for name, info in maturity.get("capabilities", {}).items():
        state = str(info.get("state", "UNKNOWN"))
        if state in {"NOT_IMPLEMENTED", "IMPLEMENTED", "BLOCKED_EXTERNAL", "HUMAN_GATE", "EXTERNAL_LICENSE", "PHYSICAL_HARDWARE", "REBOOT_LOGOFF_REQUIRED"}:
            result.append({"capability": name, "state": state})
    return result


def assess_opening() -> dict[str, Any]:
    """Assess the local kernel opening scope without starting any service."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()
    company = validate_company_manifest()
    machine = machine_detect()
    core = verify_core_cache()
    router = ModelRouter(config)
    local_ok, local_detail = router.local.health()
    acceptance = _read_json(ACCEPTANCE_FILE)
    audit = verify_ledger()

    blockers: list[str] = []
    limits: list[str] = []
    if not company.valid:
        blockers.append("COMPANY_MANIFEST_INVALID")
    if not core.get("valid"):
        blockers.append("CORE_CACHE_NOT_VERIFIED")
    if not machine.get("supported_baseline"):
        blockers.append("UNSUPPORTED_MACHINE_PROFILE")
    if config.mode in {"offline", "local"} and not local_ok:
        blockers.append("LOCAL_CONTINUITY_UNAVAILABLE")
    if not audit.get("valid"):
        blockers.append("AUDIT_LEDGER_INVALID")

    if not local_ok:
        limits.append("LOCAL_MODEL_NOT_READY")
    if not acceptance:
        limits.append("REAL_MACHINE_ACCEPTANCE_NOT_RUN")
    elif acceptance.get("result") != "PASS":
        blockers.append("REAL_MACHINE_ACCEPTANCE_FAILED")
    if acceptance and acceptance.get("hard_offline_network_state") == "NOT_TESTED":
        limits.append("HARD_OFFLINE_NOT_TESTED")

    unverified = _unverified_capabilities()
    if unverified:
        limits.append("PROFESSIONAL_ACOUSTIC_CAPABILITIES_REMAIN_UNVERIFIED_OR_INCOMPLETE")

    verified_scope = bool(
        not blockers
        and acceptance
        and acceptance.get("result") == "PASS"
        and local_ok
        and core.get("valid")
        and machine.get("supported_baseline")
    )
    if blockers:
        state = "BLOCKED"
    elif verified_scope:
        state = "OPEN_VERIFIED_SCOPE"
    else:
        state = "OPEN_WITH_LIMITS"

    return {
        "schema_version": 1,
        "assessed_at_utc": _now(),
        "operational_state": state,
        "verified_scope": "LOCAL_PORTABLE_COMPANY_KERNEL_BASELINE" if verified_scope else None,
        "company_complete": False,
        "product_truth": "operational opening is scoped and does not mean all AERIS acoustic capabilities are complete",
        "runtime_mode": config.mode,
        "local_network_scope": config.local_network_scope,
        "local_model": config.local_model,
        "local_provider_ready": local_ok,
        "local_provider_detail": local_detail,
        "machine_profile": machine.get("profile"),
        "machine_profile_supported_baseline": bool(machine.get("supported_baseline")),
        "core_integrity": core,
        "acceptance_report": str(ACCEPTANCE_FILE) if acceptance else None,
        "acceptance_result": acceptance.get("result") if acceptance else "NOT_RUN",
        "hard_offline_network_state": acceptance.get("hard_offline_network_state", "NOT_TESTED") if acceptance else "NOT_TESTED",
        "audit_ledger": audit,
        "blockers": blockers,
        "limits": sorted(set(limits)),
        "unverified_capabilities": unverified,
    }


def open_company(actor: str = "Codex Autopilot") -> dict[str, Any]:
    payload = assess_opening()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    OPENING_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ensure_expected_runs(actor=actor)
    mark_expected_run(
        "company-opening-assessment",
        payload["operational_state"] != "BLOCKED",
        error=", ".join(payload["blockers"]),
        actor=actor,
    )
    append_event("COMPANY_OPENING_ASSESSED", actor, {"operational_state": payload["operational_state"], "blockers": payload["blockers"], "limits": payload["limits"]})
    return payload


def _heartbeat_payload(port: int, opening: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "timestamp_utc": _now(),
        "pid": os.getpid(),
        "bind_host": DEFAULT_HOST,
        "port": port,
        "service": "AERIS_LOCAL_SUPERVISOR",
        "service_state": "SERVING",
        "company_opening_state": opening.get("operational_state", "UNKNOWN"),
        "company_complete": False,
    }


def _write_heartbeat(port: int, opening: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_FILE.write_text(json.dumps(_heartbeat_payload(port, opening), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        mark_expected_run("supervisor-heartbeat", True, actor="AERIS Supervisor", audit_event=False)
    except KeyError:
        ensure_expected_runs(actor="AERIS Supervisor", audit_event=False)
        mark_expected_run("supervisor-heartbeat", True, actor="AERIS Supervisor", audit_event=False)


class _Handler(BaseHTTPRequestHandler):
    server_version = "AERISLocalSupervisor/2"

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        opening = _read_json(OPENING_FILE) or assess_opening()
        _write_heartbeat(self.server.server_port, opening)  # type: ignore[attr-defined]
        if controlplane_get(self, opening):
            return
        if self.path == "/health":
            self._json(200, {
                "service": "AERIS_LOCAL_SUPERVISOR",
                "service_state": "SERVING",
                "implementation_sha": LOADED_IMPLEMENTATION_SHA,
                "pid": os.getpid(),
                "company_opening_state": opening.get("operational_state"),
                "company_complete": False,
                "scope": "loopback local supervisor heartbeat, not whole-company health proof",
            })
            return
        if self.path == "/status":
            self._json(200, opening)
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if controlplane_post(self):
            return
        if self.path != "/shutdown":
            self._json(404, {"error": "not_found"})
            return
        expected = getattr(self.server, "shutdown_token", "")  # type: ignore[attr-defined]
        supplied = self.headers.get("X-AERIS-Supervisor-Token", "")
        if not expected or not secrets.compare_digest(expected, supplied):
            self._json(403, {"error": "forbidden"})
            return
        self._json(200, {"service": "AERIS_LOCAL_SUPERVISOR", "shutdown": "accepted"})
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format: str, *args: object) -> None:
        return


def serve_supervisor(port: int = DEFAULT_PORT, heartbeat_interval_sec: int = 30) -> int:
    if not (1 <= int(port) <= 65535):
        raise ValueError("invalid supervisor port")
    opening = open_company(actor="AERIS Supervisor")
    if opening.get("operational_state") == "BLOCKED":
        print(json.dumps(opening, ensure_ascii=False, indent=2))
        return 9
    token = secrets.token_urlsafe(32)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SUPERVISOR_TOKEN_FILE.write_text(token, encoding="utf-8")
    try:
        os.chmod(SUPERVISOR_TOKEN_FILE, 0o600)
    except OSError:
        pass
    server = ThreadingHTTPServer((DEFAULT_HOST, int(port)), _Handler)
    server.shutdown_token = token  # type: ignore[attr-defined]
    supervisor_state = {
        "schema_version": 2,
        "pid": os.getpid(),
        "implementation_sha": LOADED_IMPLEMENTATION_SHA,
        "bind_host": DEFAULT_HOST,
        "port": int(port),
        "started_at_utc": _now(),
        "company_opening_state": opening.get("operational_state"),
        "public_bind_forbidden": True,
        "web_ui": f"http://{DEFAULT_HOST}:{int(port)}/",
        "api_base": f"http://{DEFAULT_HOST}:{int(port)}/api/v1/",
    }
    SUPERVISOR_FILE.write_text(json.dumps(supervisor_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_event("SUPERVISOR_STARTED", "AERIS Supervisor", {k: v for k, v in supervisor_state.items() if k != "schema_version"})

    stop = threading.Event()

    def heartbeat() -> None:
        while not stop.wait(max(5, int(heartbeat_interval_sec))):
            current = _read_json(OPENING_FILE) or opening
            _write_heartbeat(int(port), current)

    _write_heartbeat(int(port), opening)
    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        stop.set()
        server.server_close()
        append_event("SUPERVISOR_STOPPED", "AERIS Supervisor", {"pid": os.getpid(), "port": int(port)})
        try:
            SUPERVISOR_TOKEN_FILE.unlink()
        except FileNotFoundError:
            pass
    return 0


def supervisor_status(port: int = DEFAULT_PORT, timeout: float = 1.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(f"http://{DEFAULT_HOST}:{int(port)}/health", timeout=timeout) as response:
            return {"reachable": True, **json.loads(response.read().decode("utf-8"))}
    except Exception as exc:
        return {"reachable": False, "error": str(exc), "host": DEFAULT_HOST, "port": int(port)}


def start_supervisor_background(port: int = DEFAULT_PORT) -> dict[str, Any]:
    existing = supervisor_status(port)
    if existing.get("reachable"):
        return {"started": False, "already_running": True, **existing, "web_ui": f"http://{DEFAULT_HOST}:{int(port)}/"}
    log_dir = ROOT / ".aeris" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "supervisor.log"
    cmd = [sys.executable, "-m", "aeris_runtime", "company", "serve", "--port", str(int(port))]
    kwargs: dict[str, Any] = {"cwd": str(ROOT), "stdin": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        kwargs["start_new_session"] = True
    with log_path.open("ab") as log:
        process = subprocess.Popen(cmd, stdout=log, stderr=log, **kwargs)
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        status = supervisor_status(port, timeout=0.5)
        if status.get("reachable"):
            return {"started": True, "pid": process.pid, "log": str(log_path), **status, "web_ui": f"http://{DEFAULT_HOST}:{int(port)}/"}
        if process.poll() is not None:
            break
        time.sleep(0.25)
    return {"started": False, "pid": process.pid, "log": str(log_path), "error": "supervisor did not become reachable on loopback"}


def stop_supervisor(port: int = DEFAULT_PORT) -> dict[str, Any]:
    if not SUPERVISOR_TOKEN_FILE.exists():
        return {"stopped": False, "reason": "no local supervisor token; no process kill attempted"}
    token = SUPERVISOR_TOKEN_FILE.read_text(encoding="utf-8-sig").strip()
    request = urllib.request.Request(f"http://{DEFAULT_HOST}:{int(port)}/shutdown", method="POST", headers={"X-AERIS-Supervisor-Token": token})
    try:
        with urllib.request.urlopen(request, timeout=2.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"stopped": True, **payload}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {"stopped": False, "error": str(exc), "reason": "authenticated loopback shutdown failed; no blind PID kill performed"}
