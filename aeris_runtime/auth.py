"""Multi-user login for the local control plane, with one owner and any
number of owner-granted accounts scoped to specific pages/actions.

AERIS's public "intro" page (status, features, blueprint -- no live
operational data) is openly reachable, while every operational page and
API (dashboard, workspace, progress, activity, services, all business
/api/v1/* endpoints) requires a signed-in session. This module owns the
credential, permission, and session lifecycle; the route-level allow/
deny decision lives in controlplane.py.

There is exactly one **owner**: set locally via `python -m aeris_runtime
auth set-credentials` (interactive, uses getpass -- the plaintext
password is never written to disk, logged, or seen by anything other
than the person typing it). The owner has every permission, including
managing other accounts, and cannot be removed or demoted through the
API -- only by deleting .aeris/state/auth_credentials.json and running
set-credentials again, a local filesystem action.

The owner can grant any number of additional accounts (from the /admin
page or `auth grant-user`), each with an explicit subset of PERMISSIONS.
A granted account can never hold the "admin" permission -- only the
owner can manage accounts, by construction, not by a checkbox that
could be misconfigured.

Only salted PBKDF2-HMAC-SHA256 hashes are persisted, under .aeris/
(already fully gitignored) -- no plaintext password is ever stored.

Sessions are intentionally in-memory only, not persisted to disk: a
supervisor restart (the launcher does this on every run) invalidates all
sessions and requires signing in again. For a system restarted often
during development, this trades a minor inconvenience for a smaller
blast radius (a leaked session-store file would otherwise grant standing
access).
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

# Grantable permission scopes -- one per protected page/action. "admin"
# is deliberately not in this set: only the owner role carries it, and
# only implicitly (see has_permission), never as a settable flag.
GRANTABLE_PERMISSIONS = ("dashboard", "workspace", "progress", "activity", "services", "capabilities_execute")

_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}  # token -> {"username": str, "expires_at": monotonic}
_failed_attempts: list[float] = []  # monotonic timestamps of recent failed logins


def has_credentials() -> bool:
    return CREDENTIALS_PATH.is_file()


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)


def _new_user_record(password: str, role: str, permissions: list[str]) -> dict[str, Any]:
    salt = secrets.token_bytes(16)
    digest = _hash_password(password, salt)
    return {
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "hash_b64": base64.b64encode(digest).decode("ascii"),
        "iterations": PBKDF2_ITERATIONS,
        "role": role,
        "permissions": sorted(set(permissions)),
    }


def _load_store() -> dict[str, Any]:
    if not CREDENTIALS_PATH.is_file():
        return {"schema_version": 2, "users": {}}
    try:
        data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 2, "users": {}}
    if data.get("schema_version") == 1:
        # Migrate the original single-owner format transparently.
        return {"schema_version": 2, "users": {
            data["username"]: {
                "salt_b64": data["salt_b64"], "hash_b64": data["hash_b64"],
                "iterations": data.get("iterations", PBKDF2_ITERATIONS),
                "role": "owner", "permissions": list(GRANTABLE_PERMISSIONS),
            }
        }}
    return data


def _save_store(store: dict[str, Any]) -> None:
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")
    try:
        os.chmod(CREDENTIALS_PATH, 0o600)
    except OSError:
        pass


def set_credentials(username: str, password: str) -> None:
    """(Re)set the single owner account. Wipes all other accounts and
    sessions -- this is the local, filesystem-level reset path, not the
    admin API, and intentionally starts from a clean slate."""
    if not username or not username.strip():
        raise ValueError("username must not be empty")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    store = {"schema_version": 2, "users": {username.strip(): _new_user_record(password, "owner", list(GRANTABLE_PERMISSIONS))}}
    _save_store(store)
    with _lock:
        _sessions.clear()


def owner_username() -> str | None:
    store = _load_store()
    for name, record in store.get("users", {}).items():
        if record.get("role") == "owner":
            return name
    return None


def list_users() -> list[dict[str, Any]]:
    """Public-safe listing (no hashes) for the admin page."""
    store = _load_store()
    return [
        {"username": name, "role": record.get("role", "granted"), "permissions": record.get("permissions", [])}
        for name, record in sorted(store.get("users", {}).items())
    ]


def grant_user(username: str, password: str, permissions: list[str]) -> None:
    if not username or not username.strip():
        raise ValueError("username must not be empty")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    invalid = set(permissions) - set(GRANTABLE_PERMISSIONS)
    if invalid:
        raise ValueError(f"unknown permission(s): {sorted(invalid)}")
    store = _load_store()
    username = username.strip()
    existing = store.get("users", {}).get(username)
    if existing and existing.get("role") == "owner":
        raise ValueError("cannot overwrite the owner account from the admin API")
    store.setdefault("users", {})[username] = _new_user_record(password, "granted", permissions)
    _save_store(store)


def revoke_user(username: str) -> None:
    store = _load_store()
    record = store.get("users", {}).get(username)
    if record is None:
        raise ValueError("no such user")
    if record.get("role") == "owner":
        raise ValueError("cannot remove the owner account from the admin API")
    del store["users"][username]
    _save_store(store)
    with _lock:
        stale = [token for token, session in _sessions.items() if session.get("username") == username]
        for token in stale:
            del _sessions[token]


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
    store = _load_store()
    record = store.get("users", {}).get(username.strip())
    if record is None:
        # Still do a dummy hash so a nonexistent-vs-wrong-password
        # response doesn't leak via timing.
        _hash_password(password, secrets.token_bytes(16))
        _record_failed_attempt()
        return False
    salt = base64.b64decode(record["salt_b64"])
    expected = base64.b64decode(record["hash_b64"])
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, record.get("iterations", PBKDF2_ITERATIONS))
    if not secrets.compare_digest(actual, expected):
        _record_failed_attempt()
        return False
    return True


def user_permissions(username: str) -> tuple[str, list[str]] | None:
    """Returns (role, permissions) for a username, or None if unknown."""
    store = _load_store()
    record = store.get("users", {}).get(username)
    if record is None:
        return None
    role = record.get("role", "granted")
    if role == "owner":
        return role, list(GRANTABLE_PERMISSIONS) + ["admin"]
    return role, list(record.get("permissions", []))


def has_permission(username: str, permission: str) -> bool:
    result = user_permissions(username)
    if result is None:
        return False
    _role, permissions = result
    return permission in permissions


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    with _lock:
        _sessions[token] = {"username": username, "expires_at": time.monotonic() + SESSION_TTL_S}
    return token


def session_username(token: str | None) -> str | None:
    if not token:
        return None
    now = time.monotonic()
    with _lock:
        session = _sessions.get(token)
        if session is None:
            return None
        if session["expires_at"] < now:
            del _sessions[token]
            return None
        return session["username"]


def verify_session(token: str | None) -> bool:
    return session_username(token) is not None


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
