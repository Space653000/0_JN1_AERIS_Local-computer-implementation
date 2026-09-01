"""Local-only SQLite knowledge and memory index for AERIS.

Dependency-free baseline with truthful boundaries:
- versioned text documents are indexed locally;
- deleted/renamed source files are removed on rebuild;
- FTS5 is used when available, otherwise LIKE is used;
- public ingress/quarantine is never auto-indexed.

This remains a basic local text index, not the final provenance-aware acoustic knowledge system.
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Iterable

from .config import ROOT

DB_PATH = ROOT / ".aeris" / "knowledge" / "aeris.sqlite3"
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".html", ".csv"}
VERSIONED_ROOTS = ["company", "docs", "skills", "methods", "standards", "workflows", "memory", "knowledge"]
MAX_TEXT_BYTES = 5_000_000


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE IF NOT EXISTS documents (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, body TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    return db


def _ensure_fts(db: sqlite3.Connection) -> bool:
    try:
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(path UNINDEXED, body)")
        return True
    except sqlite3.OperationalError:
        return False


def _iter_files() -> Iterable[Path]:
    roots = [ROOT / name for name in VERSIONED_ROOTS]
    core = ROOT / ".aeris" / "core-reference"
    if core.exists():
        roots.append(core)
    seen: set[Path] = set()
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p in seen:
                continue
            seen.add(p)
            try:
                ok = p.is_file() and not p.is_symlink() and p.suffix.lower() in TEXT_SUFFIXES and p.stat().st_size <= MAX_TEXT_BYTES
            except OSError:
                ok = False
            if ok:
                yield p


def build_index() -> dict:
    db = _connect()
    fts = _ensure_fts(db)
    current: set[str] = set()
    indexed = 0
    unchanged = 0
    stale: list[str] = []
    total = 0
    try:
        db.execute("BEGIN")
        for p in _iter_files():
            try:
                body = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(p.relative_to(ROOT))
            current.add(rel)
            sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
            old = db.execute("SELECT sha256 FROM documents WHERE path=?", (rel,)).fetchone()
            if old and old[0] == sha:
                unchanged += 1
                continue
            db.execute(
                "INSERT INTO documents(path, sha256, body) VALUES(?,?,?) "
                "ON CONFLICT(path) DO UPDATE SET sha256=excluded.sha256, body=excluded.body",
                (rel, sha, body),
            )
            if fts:
                db.execute("DELETE FROM documents_fts WHERE path=?", (rel,))
                db.execute("INSERT INTO documents_fts(path, body) VALUES(?,?)", (rel, body))
            indexed += 1

        existing = {row[0] for row in db.execute("SELECT path FROM documents")}
        stale = sorted(existing - current)
        for rel in stale:
            db.execute("DELETE FROM documents WHERE path=?", (rel,))
            if fts:
                db.execute("DELETE FROM documents_fts WHERE path=?", (rel,))

        if fts:
            fts_count = db.execute("SELECT COUNT(*) FROM documents_fts").fetchone()[0]
            doc_count = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            if fts_count != doc_count:
                db.execute("DELETE FROM documents_fts")
                db.execute("INSERT INTO documents_fts(path, body) SELECT path, body FROM documents")

        db.commit()
        total = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {
        "indexed_or_updated": indexed,
        "unchanged": unchanged,
        "removed_stale": len(stale),
        "documents_total": total,
        "database": str(DB_PATH),
        "search_engine": "sqlite_fts5" if fts else "sqlite_like_fallback",
        "local_only": True,
    }


def _fts_query(query: str) -> str:
    tokens = [token for token in query.strip().split() if token]
    return " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)


def search(query: str, limit: int = 10) -> list[dict]:
    query = query.strip()
    if not query:
        return []
    limit = max(1, min(int(limit), 100))
    db = _connect()
    fts = _ensure_fts(db)
    rows: list[tuple[str, str]] = []
    engine = "sqlite_like_fallback"
    if fts:
        try:
            rows = db.execute(
                "SELECT path, snippet(documents_fts, 1, '', '', ' … ', 24) "
                "FROM documents_fts WHERE documents_fts MATCH ? LIMIT ?",
                (_fts_query(query), limit),
            ).fetchall()
            engine = "sqlite_fts5"
        except sqlite3.OperationalError:
            rows = []
    if not rows:
        rows = db.execute(
            "SELECT path, substr(body,1,1200) FROM documents "
            "WHERE lower(body) LIKE ? OR lower(path) LIKE ? LIMIT ?",
            (f"%{query.lower()}%", f"%{query.lower()}%", limit),
        ).fetchall()
        engine = "sqlite_like_fallback"
    db.close()
    return [{"path": path, "snippet": snippet, "search_engine": engine} for path, snippet in rows]


def stats() -> dict:
    db = _connect()
    docs = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    mem = db.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
    fts = _ensure_fts(db)
    db.close()
    return {
        "documents": docs,
        "memory_items": mem,
        "database": str(DB_PATH),
        "local_only": True,
        "search_engine": "sqlite_fts5" if fts else "sqlite_like_fallback",
        "scope": "basic_versioned_text_index_not_full_engineering_knowledge_system",
    }
