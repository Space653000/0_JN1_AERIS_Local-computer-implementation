"""P2.3 Progress history: reconstruct a percent-over-time trend from the
timestamped per-item Evidence files progress_verify already writes, rather
than a separately maintained log.

Each Evidence file already carries `item`, `result`, `candidate_sha` and
`captured_at_utc` (see progress_verify.run()). Grouping by `candidate_sha`
and taking each item's latest capture at that sha gives an honest snapshot
of "what had a PASS Evidence file when this commit was checked" -- scored
against the *current* contract's required_items list, so an item that did
not exist yet at an older sha correctly shows as not-yet-passed for that
point rather than being silently backfilled.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import ROOT
from .progress_truth import load_contract

EVIDENCE_DIR = ROOT / ".aeris" / "evidence" / "progress"


def compute_history(evidence_dir: Path | None = None) -> list[dict]:
    evidence_dir = evidence_dir or EVIDENCE_DIR
    by_sha: dict[str, dict[str, dict]] = {}
    if evidence_dir.exists():
        for path in evidence_dir.glob("*.json"):
            if path.name == "PROGRESS_TRUTH.json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            sha, item, captured = data.get("candidate_sha"), data.get("item"), data.get("captured_at_utc")
            if not sha or not item or not captured:
                continue
            bucket = by_sha.setdefault(str(sha), {})
            existing = bucket.get(item)
            if not existing or existing.get("captured_at_utc", "") < captured:
                bucket[item] = data

    try:
        required = load_contract(ROOT)["required_items"]
    except (ValueError, KeyError):
        return []

    points = []
    for sha, items in by_sha.items():
        phase_percent, item_total, pass_total = {}, 0, 0
        for phase, ids in required.items():
            passed = sum(1 for i in ids if items.get(i, {}).get("result") == "PASS")
            phase_percent[phase] = round(100 * passed / len(ids)) if ids else 0
            item_total += len(ids)
            pass_total += passed
        timestamps = [v["captured_at_utc"] for v in items.values() if v.get("captured_at_utc")]
        if not timestamps:
            continue
        points.append({
            "candidate_sha": sha,
            "captured_at_utc": max(timestamps),
            "overall_percent": round(100 * pass_total / item_total) if item_total else 0,
            "phase_percent": phase_percent,
            "items_observed": len(items),
        })
    points.sort(key=lambda p: p["captured_at_utc"])
    return points
