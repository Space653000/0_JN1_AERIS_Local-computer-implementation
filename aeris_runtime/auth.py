"""Single-owner login for the local control plane.

AERIS is moving toward a model where a public "intro" page (status,
features, blueprint -- no live operational data) is openly reachable,
while every operational page and API (dashboard, workspace, progress,
activity, services, all /api/v1/* business endpoints) requires a signed-
in session. This module owns the credential and session lifecycle; the
route-level allow/deny decision lives in controlplane.py.

Credentials are set locally by the owner via `python -m aeris_runtime
auth set-credentials` (interactive, uses getpass -- the plaintext
password is never written to disk, logged, or seen by anything other
than the person typing it). Only a salted PBKDF2-HMAC-SHA256 hash is
persisted, under .aeris/ (already fully gitignored).

Sessions are intentionally in-memory only, not persisted to disk: a
supervisor restart (the launcher does this on every run) invalidates all
sessions and requires signing in again. For a single-owner local system
restarted often during development, this is a reasonable trade --
persisting sessions would mean a stolen/leaked session-store file grants
standing access, whereas an in-memory store's blast radius ends at the
next restart.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any

from .config import ROOT

CREDENTIALS_PATH = ROOT / ".aeris" / "state" / "auth_credentials.json"
# Same file operations.py writes at supervisor startup (0600, regenerated
# every run) for the existing /shutdown endpoint. Reused here so local,
# same-machine tooling (progress_verify.py, the launcher scripts) can call
# the API without a browser session -- anyone who can read this file
# already runs as the same local OS user and could reach everything this
# login system protects some other way, so this isn't a new trust
# boundary, just formalizing the one operations.py already established.
SUPERVISOR_TOKEN_PATH = ROOT / ".aeris" / "state" / ".supervisor-token"
SUPERVISOR_TOKEN_HEADER = "X-AERIS-Supervisor-Token"
PBKDF2_ITERATIONS = 310_000
SESSION_COOKIE_NAME = "aeris_session"
SESSION_TTL_S = 12 * 3600
MAX_FAILED_ATTEMPTS = 8
LOCKOUT_WINDOW_S = 300

_lock = threading.Lock()
_sessions: dict[str, float] = {}  # token -> expires_at (monotonic)
_failed_attempts: list[float] = []  # monotonic timestamps of recent failed logins


def has_credentials() -> bool:
    return CREDENTIALS_PATH.is_file()


def set_credentials(username: str, password: str) -> None:
    if not username or not username.strip():
        raise ValueError("username must not be empty")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "username": username.strip(),
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "hash_b64": base64.b64encode(digest).decode("ascii"),
        "iterations": PBKDF2_ITERATIONS,
    }
    CREDENTIALS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        os.chmod(CREDENTIALS_PATH, 0o600)
    except OSError:
        pass
    with _lock:
        _sessions.clear()


def _load_credentials() -> dict[str, Any] | None:
    if not CREDENTIALS_PATH.is_file():
        return None
    try:
        return json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def _is_locked_out() -> bool:
    now = time.monotonic()
    with _lock:
        _failed_attempts[:] = [t for t in _failed_attempts if now - t < LOCKOUT_WINDOW_S]
        return len(_failed_attempts) >= MAX_FAILED_ATTEMPTS


def _record_failed_attempt() -> None:
    with _lock:
        _failed_attempts.append(time.monotonic())


def verify_credentials(username: str, password: str) -> bool:
    """Constant-time-ish credential check with a simple lockout window.
    Not a substitute for real rate limiting behind a reverse proxy if
    this is ever exposed publicly -- see docs/AERIS_ACCESS_CONTROL.md."""
    if _is_locked_out():
        return False
    creds = _load_credentials()
    if creds is None:
        return False
    salt = base64.b64decode(creds["salt_b64"])
    expected = base64.b64decode(creds["hash_b64"])
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, creds.get("iterations", PBKDF2_ITERATIONS))
    username_ok = secrets.compare_digest(username.strip().encode("utf-8"), creds["username"].encode("utf-8"))
    password_ok = secrets.compare_digest(actual, expected)
    if not (username_ok and password_ok):
        _record_failed_attempt()
        return False
    return True


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    with _lock:
        _sessions[token] = time.monotonic() + SESSION_TTL_S
    return token


def verify_session(token: str | None) -> bool:
    if not token:
        return False
    now = time.monotonic()
    with _lock:
        expires_at = _sessions.get(token)
        if expires_at is None:
            return False
        if expires_at < now:
            del _sessions[token]
            return False
        return True


def revoke_session(token: str | None) -> None:
    if not token:
        return
    with _lock:
        _sessions.pop(token, None)


def verify_supervisor_token(supplied: str | None) -> bool:
    if not supplied or not SUPERVISOR_TOKEN_PATH.is_file():
        return False
    try:
        expected = SUPERVISOR_TOKEN_PATH.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return False
    return bool(expected) and secrets.compare_digest(expected, supplied)


def parse_cookie(cookie_header: str | None, name: str) -> str | None:
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith(name + "="):
            return part[len(name) + 1:]
    return None
