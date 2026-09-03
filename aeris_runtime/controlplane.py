"""Local AERIS control plane: same-origin web UI + SQLite project/task APIs."""
from __future__ import annotations

import base64
import json
import mimetypes
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .audit import LEDGER_PATH
from .config import ROOT, load_config
from .expected_runs import assess_all as expected_run_health
from .knowledge import search as knowledge_search, stats as knowledge_stats
from .reproduction import reproduce_run
from .roles import get_role, invoke_role, list_roles, plan_pod
from .router import ModelRouter
from .skills_runtime import list_skills, run_skill
from .standards_registry import search_standards
from .telemetry import service_telemetry
from .machine import detect as machine_detect
from .workflow import (
    create_engineering_workflow,
    create_workflow_from_template,
    execute_workflow,
    list_workflow_templates,
    list_workflows,
    load_workflow,
)

UI_ROOT = ROOT / "ui" / "web"
DB_PATH = ROOT / ".aeris" / "control" / "control.sqlite3"
MATURITY_PATH = ROOT / "config" / "maturity.json"
IMPORT_ROOT = ROOT / ".aeris" / "imports" / "uploads"
MAX_BODY = 8_000_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


class _ClosingConnection(sqlite3.Connection):
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
                    workflow_id TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state);
                """
            )
            columns = {str(row[1]) for row in db.execute("PRAGMA table_info(tasks)").fetchall()}
            if "workflow_id" not in columns:
                db.execute("ALTER TABLE tasks ADD COLUMN workflow_id TEXT")
            if "metadata_json" not in columns:
                db.execute("ALTER TABLE tasks ADD COLUMN metadata_json TEXT")
            if db.execute("SELECT id FROM projects LIMIT 1").fetchone() is None:
                now = _now()
                db.execute(
                    "INSERT INTO projects(id,name,status,created_at,updated_at) VALUES(?,?,?,?,?)",
                    ("PRJ-AERIS-OPS", "AERIS Operations", "ACTIVE", now, now),
                )

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT p.*, (SELECT COUNT(*) FROM tasks t WHERE t.project_id=p.id) task_count FROM projects p ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def create_project(self, name: str) -> dict[str, Any]:
        name = name.strip()
        if not name:
            raise ValueError("project name is required")
        now = _now()
        pid = "PRJ-" + uuid.uuid4().hex[:10].upper()
        with self._connect() as db:
            db.execute("INSERT INTO projects(id,name,status,created_at,updated_at) VALUES(?,?,?,?,?)", (pid, name[:160], "ACTIVE", now, now))
        return {"id": pid, "name": name[:160], "status": "ACTIVE", "created_at": now, "updated_at": now, "task_count": 0}

    def list_tasks(self, project_id: str | None = None) -> list[dict[str, Any]]:
        sql, args = "SELECT * FROM tasks", ()
        if project_id:
            sql, args = sql + " WHERE project_id=?", (project_id,)
        sql += " ORDER BY updated_at DESC LIMIT 200"
        with self._connect() as db:
            rows = db.execute(sql, args).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["pod"] = json.loads(item.pop("pod_json")) if item.get("pod_json") else None
            item["metadata"] = json.loads(item.pop("metadata_json")) if item.get("metadata_json") else {}
            result.append(item)
        return result

    def create_task(self, *, project_id: str | None, title: str, description: str, risk_level: str = "R0", pod: dict[str, Any] | None = None, workflow_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        title, description = title.strip(), description.strip()
        if not title:
            raise ValueError("task title is required")
        if risk_level not in {"R0", "R1", "R2", "R3", "R4"}:
            raise ValueError("risk_level must be R0-R4")
        now, tid = _now(), "TASK-" + uuid.uuid4().hex[:12].upper()
        with self._connect() as db:
            if project_id and db.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone() is None:
                raise ValueError("unknown project_id")
            db.execute(
                "INSERT INTO tasks(id,project_id,title,description,state,risk_level,pod_json,evidence_ref,workflow_id,metadata_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (tid, project_id, title[:200], description[:20000], "DRAFT", risk_level, json.dumps(pod, ensure_ascii=False) if pod else None, None, workflow_id, json.dumps(metadata or {}, ensure_ascii=False), now, now),
            )
        return self.get_task(tid)

    def get_task(self, task_id: str) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        item = dict(row)
        item["pod"] = json.loads(item.pop("pod_json")) if item.get("pod_json") else None
        item["metadata"] = json.loads(item.pop("metadata_json")) if item.get("metadata_json") else {}
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
    if path in {"/", "/dashboard"}:
        target = UI_ROOT / "dashboard.html"
    elif path in {"/workspace", "/services"}:
        target = UI_ROOT / (path.lstrip("/") + ".html")
    elif path.startswith("/assets/"):
        rel = path[len("/assets/"):]
        if not rel or "/" in rel or "\\" in rel or ".." in rel:
            return False
        core_assets = {"aeris.css", "aeris-theme.js"}
        target = (ROOT / ".aeris" / "core-reference" / rel) if rel in core_assets else UI_ROOT / rel
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
    store, config = ControlStore(), load_config()
    router, maturity = ModelRouter(config), _json_file(MATURITY_PATH)
    local_ok, local_detail = router.local.health()
    templates = list_workflow_templates()
    workflows = list_workflows()
    maturity_counts: dict[str, int] = {}
    for item in maturity.get("capabilities", {}).values():
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
        "skill_count": len(list_skills()),
        "workflow_template_count": len(templates),
        "workflow_run_count": len(workflows),
        "workflow_count": len(workflows),
        "control": store.summary(),
        "knowledge": knowledge_stats(),
        "expected_runs": expected_run_health(),
        "maturity": {"product_stage": maturity.get("product_stage", "UNKNOWN"), "counts": maturity_counts},
        "truth": "Workflow templates are executable definitions; workflow_run_count is real instantiated runs. Neither service health nor templates imply domain verification.",
    }


def _safe_filename(name: str) -> str:
    base = Path(name).name
    safe = re.sub(r"[^A-Za-z0-9._-]", "-", base)[:120]
    if not safe or safe in {".", ".."}:
        raise ValueError("invalid upload filename")
    return safe


def _save_import(payload: dict[str, Any]) -> dict[str, Any]:
    name = _safe_filename(str(payload.get("filename", "")))
    encoded = str(payload.get("base64", ""))
    if not encoded:
        raise ValueError("base64 payload required")
    try:
        data = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("invalid base64 payload") from exc
    if not data or len(data) > 5_000_000:
        raise ValueError("uploaded file must be 1..5000000 bytes")
    IMPORT_ROOT.mkdir(parents=True, exist_ok=True)
    target = IMPORT_ROOT / (uuid.uuid4().hex[:10] + "-" + name)
    target.write_bytes(data)
    return {"path": str(target), "filename": name, "bytes": len(data), "local_only": True}


def handle_get(handler: Any, opening: dict[str, Any]) -> bool:
    from urllib.parse import urlsplit as _split
    if _split(handler.path).path.startswith("/api/v1/capabilities"):
        if urlsplit("http://"+handler.headers.get("Host","")).hostname not in {"localhost","127.0.0.1","::1"}:
            _write_json(handler,403,{"error":"loopback_host_required"}); return True
        from .engineering.api import get
        try:
            _write_json(handler,200,get(handler.path))
        except (ValueError,KeyError) as exc:
            _write_json(handler,400,{"error":str(exc)})
        except RuntimeError as exc:
            _write_json(handler,503,{"error":str(exc)})
        return True
    parsed, path = urlsplit(handler.path), urlsplit(handler.path).path
    if _serve_ui(handler, path):
        return True
    if not path.startswith("/api/v1/"):
        return False
    qs = parse_qs(parsed.query)
    try:
        if path == "/api/v1/status":
            _write_json(handler, 200, _status(opening))
        elif path == "/api/v1/roles":
            roles = list_roles(); _write_json(handler, 200, {"count": len(roles), "roles": roles})
        elif path.startswith("/api/v1/roles/"):
            _write_json(handler, 200, get_role(path.rsplit("/", 1)[-1]))
        elif path == "/api/v1/projects":
            _write_json(handler, 200, {"projects": ControlStore().list_projects()})
        elif path == "/api/v1/tasks":
            _write_json(handler, 200, {"tasks": ControlStore().list_tasks((qs.get("project_id") or [None])[0])})
        elif path == "/api/v1/skills":
            _write_json(handler, 200, {"skills": list_skills()})
        elif path == "/api/v1/workflow-templates":
            templates = list_workflow_templates(); _write_json(handler, 200, {"count": len(templates), "templates": templates})
        elif path == "/api/v1/workflows":
            _write_json(handler, 200, {"workflows": list_workflows()})
        elif path.startswith("/api/v1/workflows/"):
            _write_json(handler, 200, load_workflow(path.rsplit("/", 1)[-1]))
        elif path == "/api/v1/standards":
            _write_json(handler, 200, {"query": (qs.get("q") or [""])[0], "standards": search_standards((qs.get("q") or [""])[0])})
        elif path == "/api/v1/expected-runs":
            _write_json(handler, 200, expected_run_health())
        elif path == "/api/v1/knowledge/search":
            query = (qs.get("q") or [""])[0]; limit = int((qs.get("limit") or ["10"])[0])
            _write_json(handler, 200, {"query": query, "results": knowledge_search(query, limit)})
        elif path == "/api/v1/maturity":
            _write_json(handler, 200, _json_file(MATURITY_PATH))
        elif path == "/api/v1/services":
            _write_json(handler, 200, service_telemetry(ControlStore().summary()))
        elif path == "/api/v1/machine":
            _write_json(handler, 200, machine_detect())
        elif path == "/api/v1/audit":
            _write_json(handler, 200, {"records": _audit_recent(int((qs.get("limit") or ["50"])[0]))})
        else:
            _write_json(handler, 404, {"error": "api_not_found"})
        return True
    except KeyError as exc:
        _write_json(handler, 404, {"error": "not_found", "detail": str(exc)}); return True
    except (ValueError, TypeError) as exc:
        _write_json(handler, 400, {"error": "bad_request", "detail": str(exc)}); return True
    except Exception as exc:
        _write_json(handler, 500, {"error": "internal_error", "detail": type(exc).__name__}); return True


def handle_post(handler: Any) -> bool:
    path = urlsplit(handler.path).path
    if not path.startswith("/api/v1/"):
        return False
    if path.startswith("/api/v1/capabilities/"):
        host=handler.headers.get("Host",""); origin=handler.headers.get("Origin")
        if urlsplit("http://"+host).hostname not in {"localhost","127.0.0.1","::1"} or origin and origin!="http://"+host or not handler.headers.get("Content-Type","").lower().startswith("application/json"):
            _write_json(handler,403,{"error":"same_origin_json_required"}); return True
    try:
        payload = _body(handler)
        if path == "/api/v1/projects":
            _write_json(handler, 201, ControlStore().create_project(str(payload.get("name", ""))))
        elif path == "/api/v1/tasks":
            query = str(payload.get("description") or payload.get("title") or "")
            pod = plan_pod(query, int(payload.get("max_roles", 8))) if payload.get("auto_pod", True) else None
            metadata = payload.get("metadata") or {}
            if not isinstance(metadata, dict):
                raise ValueError("metadata must be an object")
            workflow = None
            if payload.get("create_workflow"):
                workflow = create_engineering_workflow(
                    str(payload.get("title", "")), str(payload.get("actor", "Local UI")),
                    description=str(payload.get("description", "")), risk=str(payload.get("risk_level", "R0")),
                    skill_id=payload.get("skill_id"), skill_params=payload.get("skill_params") or {},
                    max_roles=int(payload.get("max_roles", 8)),
                )
            task = ControlStore().create_task(
                project_id=payload.get("project_id"), title=str(payload.get("title", "")),
                description=str(payload.get("description", "")), risk_level=str(payload.get("risk_level", "R0")),
                pod=pod, workflow_id=str(workflow.get("workflow_id")) if workflow else None, metadata=metadata,
            )
            _write_json(handler, 201, {"task": task, "workflow": workflow} if workflow else task)
        elif path == "/api/v1/pods/plan":
            if payload.get("needed_skills"):
                from .engineering.orchestration import route_pod
                _write_json(handler,200,route_pod(payload))
            else:
                _write_json(handler, 200, plan_pod(str(payload.get("query", "")), int(payload.get("max_roles", 8))))
        elif path.startswith("/api/v1/capabilities/"):
            from .engineering.api import post
            _write_json(handler,200,post(path,payload))
        elif path.startswith("/api/v1/roles/") and path.endswith("/invoke"):
            refs = payload.get("evidence_refs", [])
            if not isinstance(refs, list) or any(not isinstance(x, str) for x in refs):
                raise ValueError("evidence_refs must be a list of strings")
            _write_json(handler, 200, invoke_role(path.split("/")[-2], str(payload.get("prompt", "")), evidence_refs=refs))
        elif path == "/api/v1/imports":
            _write_json(handler, 201, _save_import(payload))
        elif path == "/api/v1/skills/run":
            skill_id = str(payload.get("skill_id", "")); params = payload.get("params")
            if not isinstance(params, dict):
                raise ValueError("params must be an object")
            _write_json(handler, 200, run_skill(skill_id, params))
        elif path == "/api/v1/workflows/from-template":
            params = payload.get("skill_params")
            if not isinstance(params, dict):
                raise ValueError("skill_params must be an object")
            _write_json(handler, 201, create_workflow_from_template(
                str(payload.get("template_id", "")),
                str(payload.get("actor", "Local UI")),
                summary=str(payload.get("summary", "")),
                description=str(payload.get("description", "")),
                skill_params=params,
                max_roles=int(payload.get("max_roles", 8)),
            ))
        elif path == "/api/v1/workflows":
            params = payload.get("skill_params")
            if params is not None and not isinstance(params, dict):
                raise ValueError("skill_params must be an object")
            _write_json(handler, 201, create_engineering_workflow(str(payload.get("summary", "")), str(payload.get("actor", "Local UI")), description=str(payload.get("description", "")), risk=str(payload.get("risk", "R0")), skill_id=payload.get("skill_id"), skill_params=params or {}, max_roles=int(payload.get("max_roles", 8))))
        elif path.startswith("/api/v1/workflows/") and path.endswith("/execute"):
            _write_json(handler, 200, execute_workflow(path.split("/")[-2], str(payload.get("actor", "Local UI"))))
        elif path.startswith("/api/v1/reproduction/"):
            _write_json(handler, 200, reproduce_run(path.rsplit("/", 1)[-1]))
        else:
            _write_json(handler, 404, {"error": "api_not_found"})
        return True
    except KeyError as exc:
        _write_json(handler, 404, {"error": "not_found", "detail": str(exc)}); return True
    except (ValueError, TypeError) as exc:
        _write_json(handler, 400, {"error": "bad_request", "detail": str(exc)}); return True
    except Exception as exc:
        _write_json(handler, 500, {"error": "internal_error", "detail": type(exc).__name__}); return True
