"""Evidence-backed AERIS progress evaluation.

This module deliberately separates the progress contract from observations.
Missing or conflicting evidence never becomes optimistic progress.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

CANONICAL_AUTHORITY_SHA = "64576bdbe680170fc1ea27306d1a2ab494cac733"
ALLOWED_SCORES = {0, 20, 40, 60, 80, 90, 100}
PROVENANCE_FIELDS = (
    "authority_sha",
    "source_sha",
    "evidence_type",
    "evidence_pointer",
    "result",
    "observed_at",
)


@dataclass(frozen=True)
class ProgressEvaluation:
    state: str
    overall_percent: int | None
    phase_percent: dict[str, int | None]
    item_scores: dict[str, int | None]
    errors: tuple[str, ...]


def _valid_observed_at(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def evaluate_progress(contract: dict[str, Any], observations: dict[str, Any]) -> ProgressEvaluation:
    """Evaluate machine-readable observations against the canonical contract.

    UNKNOWN means evidence is absent/incomplete. FAIL_CLOSED means evidence is
    contradictory or violates authority/schema constraints. Neither state may
    be represented as product completion.
    """
    errors: list[str] = []
    authority = contract.get("authority") or {}
    if authority.get("blueprint_commit") != CANONICAL_AUTHORITY_SHA:
        return ProgressEvaluation("FAIL_CLOSED", None, {}, {}, ("authority_mismatch",))

    required = contract.get("required_items")
    if not isinstance(required, dict) or not required:
        return ProgressEvaluation("FAIL_CLOSED", None, {}, {}, ("required_items_missing",))

    raw_items = observations.get("items")
    if not isinstance(raw_items, dict):
        raw_items = {}

    item_scores: dict[str, int | None] = {}
    phase_scores: dict[str, int | None] = {}
    seen_required: set[str] = set()

    for phase, item_ids in required.items():
        if not isinstance(item_ids, list) or not item_ids:
            errors.append(f"invalid_required_phase:{phase}")
            phase_scores[str(phase)] = None
            continue
        scores: list[int] = []
        for item_id in item_ids:
            item_id = str(item_id)
            if item_id in seen_required:
                errors.append(f"duplicate_required_item:{item_id}")
            seen_required.add(item_id)
            record = raw_items.get(item_id)
            if not isinstance(record, dict):
                item_scores[item_id] = None
                continue
            missing = [field for field in PROVENANCE_FIELDS if not record.get(field)]
            if missing:
                item_scores[item_id] = None
                continue
            if record.get("authority_sha") != CANONICAL_AUTHORITY_SHA:
                errors.append(f"authority_mismatch:{item_id}")
                item_scores[item_id] = None
                continue
            if not _valid_observed_at(record.get("observed_at")):
                errors.append(f"invalid_observed_at:{item_id}")
                item_scores[item_id] = None
                continue
            score = record.get("score")
            if score not in ALLOWED_SCORES:
                errors.append(f"invalid_score:{item_id}")
                item_scores[item_id] = None
                continue
            item_scores[item_id] = int(score)
            scores.append(int(score))
        phase_scores[str(phase)] = round(sum(scores) / len(item_ids)) if len(scores) == len(item_ids) else None

    unexpected = sorted(set(raw_items) - seen_required)
    if unexpected:
        errors.append("unexpected_items:" + ",".join(unexpected))

    if errors:
        return ProgressEvaluation("FAIL_CLOSED", None, phase_scores, item_scores, tuple(errors))
    if any(score is None for score in item_scores.values()) or len(item_scores) != len(seen_required):
        return ProgressEvaluation("UNKNOWN", None, phase_scores, item_scores, ())

    scores = [score for score in item_scores.values() if score is not None]
    overall = round(sum(scores) / len(scores))
    if overall == 100 and observations.get("p6_comprehensive_acceptance") != "PASS":
        return ProgressEvaluation("FAIL_CLOSED", None, phase_scores, item_scores, ("p6_acceptance_required_for_100",))
    return ProgressEvaluation("VALID", overall, phase_scores, item_scores, ())
