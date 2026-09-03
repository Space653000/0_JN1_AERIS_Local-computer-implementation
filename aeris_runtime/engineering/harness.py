"""Append-only, hash-chained Memory. It cannot overwrite raw Evidence."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ..config import ROOT
from ..evidence import validate_bundle
from .catalog import canonical, digest

KINDS={"HOT_CONTEXT","STRUCTURED_KNOWLEDGE","PROJECT_MEMORY","EXPERIMENT_MEMORY","DECISION_MEMORY",
       "LESSON_MEMORY","INSIGHT","RETROSPECTIVE","CROSS_ROLE_REVIEW","CONSENSUS_DISAGREEMENT",
       "FAILURE_LIBRARY","KNOWLEDGE_DISTILLATION","SKILL_USAGE","GOLDEN_REGRESSION"}
DB=ROOT/".aeris"/"capability-factory"/"harness.sqlite3"


class ClosingConnection(sqlite3.Connection):
    def __exit__(self,exc_type,exc,tb):
        try: return super().__exit__(exc_type,exc,tb)
        finally: self.close()


class Harness:
    def __init__(self,path: Path|None=None):
        self.path=path or DB
        if not self.path.resolve().is_relative_to(ROOT.resolve()): raise ValueError("Memory database outside AERIS root")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    project TEXT NOT NULL, kind TEXT NOT NULL, actor TEXT NOT NULL,
                    created_at TEXT NOT NULL, payload TEXT NOT NULL,
                    previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE);
                CREATE TRIGGER IF NOT EXISTS immutable_events_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT,'Memory event history is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_events_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT,'Memory event history is append-only'); END;
            """)

    def connect(self):
        conn=sqlite3.connect(self.path,timeout=30,factory=ClosingConnection); conn.row_factory=sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL"); return conn

    def append(self,project: str,kind: str,payload: dict,actor: str):
        if kind not in KINDS or not project.strip() or not actor.strip(): raise ValueError("valid project, memory kind and actor required")
        if not isinstance(payload,dict) or len(canonical(payload))>1_000_000: raise ValueError("bounded object memory payload required")
        for run in payload.get("evidence_run_ids",[]):
            if not validate_bundle(run).get("valid"): raise ValueError("Memory cannot cite a missing or tampered Evidence bundle")
        payload={**payload,"memory_is_evidence":False}
        event={"project":project,"kind":kind,"actor":actor,"created_at":datetime.now(timezone.utc).isoformat(),"payload":payload}
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            last=conn.execute("SELECT event_hash FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
            previous=last[0] if last else "0"*64
            event_hash=digest({**event,"previous_hash":previous})
            cursor=conn.execute("INSERT INTO events(project,kind,actor,created_at,payload,previous_hash,event_hash) VALUES(?,?,?,?,?,?,?)",
                                (project,kind,actor,event["created_at"],canonical(payload).decode(),previous,event_hash))
            return {"sequence":cursor.lastrowid,**event,"previous_hash":previous,"event_hash":event_hash}

    def events(self,project: str,limit=200):
        with self.connect() as conn:
            rows=conn.execute("SELECT * FROM events WHERE project=? ORDER BY sequence DESC LIMIT ?",(project,max(1,min(int(limit),10000)))).fetchall()
            return [{**dict(r),"payload":json.loads(r["payload"])} for r in reversed(rows)]

    def verify(self):
        with self.connect() as conn:
            rows=conn.execute("SELECT * FROM events ORDER BY sequence").fetchall()
        previous="0"*64
        for row in rows:
            event={k:row[k] for k in ("project","kind","actor","created_at")}; event["payload"]=json.loads(row["payload"])
            if row["previous_hash"]!=previous or row["event_hash"]!=digest({**event,"previous_hash":previous}):
                return {"valid":False,"first_bad_sequence":row["sequence"]}
            previous=row["event_hash"]
        return {"valid":True,"events":len(rows),"last_hash":previous,"scope":"application append-only hash chain; not administrator-proof WORM"}

    def context(self,project):
        events=self.events(project)
        by_kind={kind:[] for kind in sorted(KINDS)}
        for event in events: by_kind[event["kind"]].append(event)
        usage=Counter(e["payload"].get("skill_id") for e in events if e["kind"]=="SKILL_USAGE")
        return {"project":project,"hot_context":events[-12:],"memories":by_kind,"skill_usage":dict(usage),
                "memory_is_evidence":False,"chain":self.verify()}

    def distill(self,project):
        events=self.events(project)
        failures=[e for e in events if e["kind"] in {"FAILURE_LIBRARY","CONSENSUS_DISAGREEMENT"}]
        result={"source_event_hashes":[e["event_hash"] for e in events],"observed_events":len(events),
                "failure_count":len(failures),"lesson":"Retain failed runs and distinguish analytical baselines from calibrated measurements.",
                "method":"deterministic event aggregation; no LLM promotion of Memory to Evidence"}
        self.append(project,"RETROSPECTIVE",result,"AERIS Harness")
        self.append(project,"INSIGHT",{"source_event_hashes":result["source_event_hashes"],"failure_count":len(failures),"interpretation":"Disagreements and failures require a discriminating follow-up test, not a consensus-only conclusion."},"AERIS Harness")
        self.append(project,"KNOWLEDGE_DISTILLATION",result,"AERIS Harness")
        return result
