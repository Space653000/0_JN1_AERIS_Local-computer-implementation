"""AERIS local standards registry.

Registry entries are useful for discovery even when not live-verified, but formal-use
lookup fails closed unless the exact edition/status has been explicitly verified.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import ROOT

REGISTRY_PATH = ROOT / "standards" / "registry.v1.json"


def load_registry() -> dict[str, Any]:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1 or not isinstance(data.get("standards"), list):
        raise ValueError("invalid standards registry")
    return data


def list_standards() -> list[dict[str, Any]]:
    return list(load_registry()["standards"])


def search_standards(query: str) -> list[dict[str, Any]]:
    q = query.strip().lower()
    if not q:
        return list_standards()
    return [
        item for item in list_standards()
        if q in str(item.get("standard_id", "")).lower()
        or q in str(item.get("title", "")).lower()
        or q in " ".join(str(x) for x in item.get("keywords", [])).lower()
    ]


def require_formal_use(standard_id: str) -> dict[str, Any]:
    matches = [s for s in list_standards() if str(s.get("standard_id", "")).lower() == standard_id.strip().lower()]
    if not matches:
        raise KeyError(standard_id)
    item = matches[0]
    if item.get("verification_state") != "LIVE_VERIFIED" or not item.get("verified_at_utc") or not item.get("source_url"):
        raise RuntimeError(f"STANDARD_NOT_LIVE_VERIFIED_FOR_FORMAL_USE: {standard_id}")
    return item
