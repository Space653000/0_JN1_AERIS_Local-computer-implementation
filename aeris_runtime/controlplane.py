"""Local AERIS control plane: same-origin web UI + SQLite project/task APIs.

Dependency-free on purpose so a supported local machine can serve the company control
surface immediately after the portable runtime is installed. All endpoints bind through
the loopback-only supervisor in operations.py.
"""
from __future__ import annotations

import json
import mimetypes
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .audit import LEDGER_PATH
from .config import ROOT, load_config
from .knowledge import search as knowledge_search, stats as knowledge_stats
from .roles import get_role, invoke_role, list_roles, plan_pod
from .router import ModelRouter

UI_ROOT = ROOT / "ui" / "web"
DB_PATH = ROOT / ".aeris" / "control" / "control.sqlite3"
MATURITY_PATH = ROOT / "config" / "maturity.json"
MAX_BODY = 1_000_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


class _ClosingConnection(sqlite3.Connection):
    """sqlite3 context manager that actually closes the OS handle on exit."""
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        try:
            return bool(super().__exit__(exc_type, exc, tb))
        finally:
            self.close()


class ControlStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db_path, factory=_ClosingConnection)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _ensure(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    state TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    pod_json TEXT,
                    evidence_ref TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state);
                """
            )
            row = db.execute("SELECT id FROM projects LIMIT 1").fetchone()
            if row is None:
                now = _now()
                db.execute(
                    "INSERT INTO projects(id,name,status,created_at,updated_at) VALUES(?,?,?,?,?)",
                    ("PRJ-AERIS-OPS", "AERIS Operations", "ACTIVE", now, now),
                )

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT p.*, (SELECT COUNT(*) FROM tasks t WHERE t.project_id=p.id) task_count "
                "FROM projects p ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def create_project(self, name: str) -> dict[str, Any]:
        name = name.strip()
        if not name:
            raise ValueError("project name is required")
        now = _now()
        pid = "PRJ-" + uuid.uuid4().hex[:10].upper()
        with self._connect() as db:
            db.execute(
                "INSERT INTO projects(id,name,status,created_at,updated_at) VALUES(?,?,?,?,?)",
                (pid, name[:160], "ACTIVE", now, now),
            )
        return {"id": pid, "name": name[:160], "status": "ACTIVE", "created_at": now, "updated_at": now, "task_count": 0}

    def list_tasks(self, project_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM tasks"
        args: tuple[Any, ...] = ()
        if project_id:
            sql += " WHERE project_id=?"
            args = (project_id,)
        sql += " ORDER BY updated_at DESC LIMIT 200"
        with self._connect() as db:
            rows = db.execute(sql, args).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["pod"] = json.loads(item.pop("pod_json")) if item.get("pod_json") else None
            result.append(item)
        return result

    def create_task(self, *, project_id: str | None, title: str, description: str, risk_level: str = "R0", pod: dict[str, Any] | None = None) -> dict[str, Any]:
        title = title.strip()
        description = description.strip()
        if not title:
            raise ValueError("task title is required")
        if risk_level not in {"R0", "R1", "R2", "R3", "R4"}:
            raise ValueError("risk_level must be R0-R4")
        now = _now()
        tid = "TASK-" + uuid.uuid4().hex[:12].upper()
        with self._connect() as db:
            if project_id and db.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone() is None:
                raise ValueError("unknown project_id")
            db.execute(
                "INSERT INTO tasks(id,project_id,title,description,state,risk_level,pod_json,evidence_ref,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (tid, project_id, title[:200], description[:20000], "DRAFT", risk_level, json.dumps(pod, ensure_ascii=False) if pod else None, None, now, now),
            )
        return self.get_task(tid)

    def get_task(self, task_id: str) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        item = dict(row)
        item["pod"] = json.loads(item.pop("pod_json")) if item.get("pod_json") else None
        return item

    def summary(self) -> dict[str, int]:
        with self._connect() as db:
            projects = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            tasks = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            active = db.execute("SELECT COUNT(*) FROM tasks WHERE state NOT IN ('RELEASED','CANCELLED')").fetchone()[0]
        return {"projects": projects, "tasks": tasks, "active_tasks": active}


def _write_json(handler: Any, code: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    handler.wfile.write(body)


def _write_bytes(handler: Any, code: int, body: bytes, content_type: str) -> None:
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Frame-Options", "DENY")
    handler.send_header("Referrer-Policy", "no-referrer")
    handler.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'")
    handler.end_headers()
    handler.wfile.write(body)


def _body(handler: Any) -> dict[str, Any]:
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except ValueError as exc:
        raise ValueError("invalid Content-Length") from exc
    if length <= 0 or length > MAX_BODY:
        raise ValueError("request body missing or too large")
    raw = handler.rfile.read(length)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid JSON body") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    return payload


def _serve_ui(handler: Any, path: str) -> bool:
    if path in {"/", "/dashboard", "/workspace", "/services"}:
        target = UI_ROOT / "index.html"
    elif path.startswith("/assets/"):
        rel = path[len("/assets/"):]
        if not rel or "/" in rel or "\\" in rel or ".." in rel:
            return False
        target = UI_ROOT / rel
    else:
        return False
    if not target.is_file():
        _write_json(handler, 503, {"error": "ui_asset_missing", "path": str(target)})
        return True
    mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    if target.suffix == ".js":
        mime = "application/javascript; charset=utf-8"
    elif target.suffix in {".html", ".css"}:
        mime += "; charset=utf-8"
    _write_bytes(handler, 200, target.read_bytes(), mime)
    return True


def _audit_recent(limit: int = 50) -> list[dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    lines = LEDGER_PATH.read_text(encoding="utf-8-sig", errors="replace").splitlines()[-max(1, min(limit, 200)):]
    result = []
    for line in reversed(lines):
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            result.append({"invalid_record": True, "raw": line[:400]})
    return result


def _status(opening: dict[str, Any]) -> dict[str, Any]:
    store = ControlStore()
    kstats = knowledge_stats()
    config = load_config()
    router = ModelRouter(config)
    local_ok, local_detail = router.local.health()
    maturity = _json_file(MATURITY_PATH)
    caps = maturity.get("capabilities", {})
    maturity_counts: dict[str, int] = {}
    for item in caps.values():
        state = str(item.get("state", "UNKNOWN"))
        maturity_counts[state] = maturity_counts.get(state, 0) + 1
    return {
        "service": "AERIS_LOCAL_CONTROL_PLANE",
        "company_opening_state": opening.get("operational_state", "UNKNOWN"),
        "company_complete": False,
        "runtime_mode": config.mode,
        "local_model": config.local_model,
        "local_provider_ready": local_ok,
        "local_provider_detail": local_detail,
        "role_count": len(list_roles()),
        "control": store.summary(),
        "knowledge": kstats,
        "maturity": {"product_stage": maturity.get("product_stage", "UNKNOWN"), "counts": maturity_counts},
        "truth": "This is the live local control plane. OPEN/serving does not imply every acoustic capability is domain-verified.",
    }


def handle_get(handler: Any, opening: dict[str, Any]) -> bool:
    parsed = urlsplit(handler.path)
    path = parsed.path
    if _serve_ui(handler, path):
        return True
    if not path.startswith("/api/v1/"):
        return False
    qs = parse_qs(parsed.query)
    try:
        if path == "/api/v1/status":
            _write_json(handler, 200, _status(opening))
        elif path == "/api/v1/roles":
            roles = list_roles()
            _write_json(handler, 200, {"count": len(roles), "roles": roles})
        elif path.startswith("/api/v1/roles/"):
            _write_json(handler, 200, get_role(path.rsplit("/", 1)[-1]))
        elif path == "/api/v1/projects":
            _write_json(handler, 200, {"projects": ControlStore().list_projects()})
        elif path == "/api/v1/tasks":
            project_id = (qs.get("project_id") or [None])[0]
            _write_json(handler, 200, {"tasks": ControlStore().list_tasks(project_id)})
        elif path == "/api/v1/knowledge/search":
            query = (qs.get("q") or [""])[0]
            limit = int((qs.get("limit") or ["10"])[0])
            _write_json(handler, 200, {"query": query, "results": knowledge_search(query, limit)})
        elif path == "/api/v1/maturity":
            _write_json(handler, 200, _json_file(MATURITY_PATH))
        elif path == "/api/v1/audit":
            limit = int((qs.get("limit") or ["50"])[0])
            _write_json(handler, 200, {"records": _audit_recent(limit)})
        else:
            _write_json(handler, 404, {"error": "api_not_found"})
        return True
    except KeyError as exc:
        _write_json(handler, 404, {"error": "not_found", "detail": str(exc)})
        return True
    except (ValueError, TypeError) as exc:
        _write_json(handler, 400, {"error": "bad_request", "detail": str(exc)})
        return True
    except Exception as exc:
        _write_json(handler, 500, {"error": "internal_error", "detail": type(exc).__name__})
        return True


def handle_post(handler: Any) -> bool:
    parsed = urlsplit(handler.path)
    path = parsed.path
    if not path.startswith("/api/v1/"):
        return False
    try:
        payload = _body(handler)
        if path == "/api/v1/projects":
            item = ControlStore().create_project(str(payload.get("name", "")))
            _write_json(handler, 201, item)
        elif path == "/api/v1/tasks":
            query = str(payload.get("description") or payload.get("title") or "")
            pod = plan_pod(query, int(payload.get("max_roles", 8))) if payload.get("auto_pod", True) else None
            item = ControlStore().create_task(
                project_id=payload.get("project_id"),
                title=str(payload.get("title", "")),
                description=str(payload.get("description", "")),
                risk_level=str(payload.get("risk_level", "R0")),
                pod=pod,
            )
            _write_json(handler, 201, item)
        elif path == "/api/v1/pods/plan":
            _write_json(handler, 200, plan_pod(str(payload.get("query", "")), int(payload.get("max_roles", 8))))
        elif path.startswith("/api/v1/roles/") and path.endswith("/invoke"):
            role_id = path.split("/")[-2]
            _write_json(handler, 200, invoke_role(role_id, str(payload.get("prompt", ""))))
        else:
            _write_json(handler, 404, {"error": "api_not_found"})
        return True
    except KeyError as exc:
        _write_json(handler, 404, {"error": "not_found", "detail": str(exc)})
        return True
    except (ValueError, TypeError) as exc:
        _write_json(handler, 400, {"error": "bad_request", "detail": str(exc)})
        return True
    except Exception as exc:
        _write_json(handler, 500, {"error": "internal_error", "detail": type(exc).__name__})
        return True
