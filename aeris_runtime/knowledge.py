"""Local-only SQLite knowledge and memory index for AERIS."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Iterable

from .config import ROOT

DB_PATH = ROOT / ".aeris" / "knowledge" / "aeris.sqlite3"
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".html", ".csv"}
VERSIONED_ROOTS = ["company", "docs", "skills", "methods", "standards", "workflows", "memory", "knowledge"]


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS documents (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, body TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    return db


def _iter_files() -> Iterable[Path]:
    roots = [ROOT / name for name in VERSIONED_ROOTS]
    core = ROOT / ".aeris" / "core-reference"
    if core.exists():
        roots.append(core)
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and p.stat().st_size <= 5_000_000:
                yield p


def build_index() -> dict:
    db = _connect()
    count = 0
    for p in _iter_files():
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(p.relative_to(ROOT))
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        db.execute(
            "INSERT INTO documents(path, sha256, body) VALUES(?,?,?) ON CONFLICT(path) DO UPDATE SET sha256=excluded.sha256, body=excluded.body",
            (rel, sha, body),
        )
        count += 1
    db.commit()
    total = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    db.close()
    return {"indexed_this_run": count, "documents_total": total, "database": str(DB_PATH)}


def search(query: str, limit: int = 10) -> list[dict]:
    db = _connect()
    rows = db.execute(
        "SELECT path, substr(body,1,1200) FROM documents WHERE lower(body) LIKE ? OR lower(path) LIKE ? LIMIT ?",
        (f"%{query.lower()}%", f"%{query.lower()}%", limit),
    ).fetchall()
    db.close()
    return [{"path": path, "snippet": snippet} for path, snippet in rows]


def stats() -> dict:
    db = _connect()
    docs = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    mem = db.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
    db.close()
    return {"documents": docs, "memory_items": mem, "database": str(DB_PATH), "local_only": True}
