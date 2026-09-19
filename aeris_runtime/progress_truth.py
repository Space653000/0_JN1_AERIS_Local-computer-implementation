"""Fail-closed evaluator for the Progress Center's machine-readable evidence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .config import ROOT

CANONICAL_AUTHORITY_SHA = "64576bdbe680170fc1ea27306d1a2ab494cac733"
ALLOWED_SCORES = {0, 20, 40, 60, 80, 90, 100}
RESULTS = {"PASS", "PARTIAL", "BLOCKED", "FAIL", "NOT_VERIFIED"}
PROVENANCE_FIELDS = (
    "authority_sha", "source_sha", "evidence_type", "evidence_pointer", "result", "observed_at",
)
DEFAULT_OBSERVATION_PATH = Path(".aeris") / "evidence" / "progress" / "PROGRESS_TRUTH.json"


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
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def load_contract(root: Path = ROOT) -> dict[str, Any]:
    """Load the versioned Progress Truth contract; malformed input fails closed."""
    try:
        value = json.loads((root / "config" / "progress_truth.v1.json").read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("progress_truth_contract_unreadable") from exc
    if not isinstance(value, dict):
        raise ValueError("progress_truth_contract_invalid")
    return value


def load_observations(root: Path = ROOT) -> dict[str, Any]:
    """Load local-only observations. An absent file is unknown, never a PASS."""
    path = root / DEFAULT_OBSERVATION_PATH
    if not path.exists():
        return {"items": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"items": {}, "_load_error": "observations_unreadable"}
    return value if isinstance(value, dict) else {"items": {}, "_load_error": "observations_invalid"}


def _evidence_pointer_exists(pointer: Any, root: Path) -> bool:
    if not isinstance(pointer, str) or not pointer.strip():
        return False
    try:
        target = (root / pointer).resolve()
        target.relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return target.is_file()


def evaluate_progress(
    contract: dict[str, Any],
    observations: dict[str, Any],
    *,
    runtime_sha: str | None = None,
    evidence_root: Path | None = None,
) -> ProgressEvaluation:
    """Evaluate evidence records without allowing absent or contradictory facts to inflate progress."""
    authority = contract.get("authority") or {}
    if authority.get("blueprint_commit") != CANONICAL_AUTHORITY_SHA:
        return ProgressEvaluation("FAIL_CLOSED", None, {}, {}, ("authority_mismatch",))
    required = contract.get("required_items")
    if not isinstance(required, dict) or not required:
        return ProgressEvaluation("FAIL_CLOSED", None, {}, {}, ("required_items_missing",))

    raw_items = observations.get("items")
    raw_items = raw_items if isinstance(raw_items, dict) else {}
    errors: list[str] = [str(observations["_load_error"])] if observations.get("_load_error") else []
    scores: dict[str, int | None] = {}
    phases: dict[str, int | None] = {}
    seen: set[str] = set()
    for phase, item_ids in required.items():
        if not isinstance(item_ids, list) or not item_ids:
            errors.append(f"invalid_required_phase:{phase}")
            phases[str(phase)] = None
            continue
        phase_scores: list[int] = []
        for item_id in item_ids:
            item_id = str(item_id)
            if item_id in seen:
                errors.append(f"duplicate_required_item:{item_id}")
            seen.add(item_id)
            record = raw_items.get(item_id)
            if not isinstance(record, dict):
                scores[item_id] = None
                phase_scores.append(0)
                continue
            expected_fields = contract.get("observation_required_fields", PROVENANCE_FIELDS)
            if not isinstance(expected_fields, list) or any(field not in record for field in expected_fields):
                scores[item_id] = None
                phase_scores.append(0)
                continue
            missing = [field for field in PROVENANCE_FIELDS if not record.get(field)]
            if missing:
                scores[item_id] = None
                phase_scores.append(0)
                continue
            if record["authority_sha"] != CANONICAL_AUTHORITY_SHA:
                errors.append(f"authority_mismatch:{item_id}")
            if not _valid_observed_at(record["observed_at"]):
                errors.append(f"invalid_observed_at:{item_id}")
            if runtime_sha and record["source_sha"] != runtime_sha:
                errors.append(f"source_runtime_mismatch:{item_id}")
            if evidence_root and not _evidence_pointer_exists(record["evidence_pointer"], evidence_root):
                errors.append(f"evidence_pointer_missing:{item_id}")
            score = record.get("score")
            if score not in ALLOWED_SCORES:
                errors.append(f"invalid_score:{item_id}")
                scores[item_id] = None
                phase_scores.append(0)
                continue
            result = record["result"]
            if result not in RESULTS:
                errors.append(f"invalid_result:{item_id}")
            elif (result == "PASS" and score != 100) or (result in {"BLOCKED", "FAIL"} and score != 0):
                errors.append(f"result_score_conflict:{item_id}")
            scores[item_id] = int(score)
            phase_scores.append(int(score))
        phases[str(phase)] = round(sum(phase_scores) / len(item_ids))

    unexpected = sorted(set(raw_items) - seen)
    if unexpected:
        errors.append("unexpected_items:" + ",".join(unexpected))
    if errors:
        return ProgressEvaluation("FAIL_CLOSED", None, phases, scores, tuple(errors))
    overall = round(sum(score or 0 for score in scores.values()) / len(seen))
    if overall == 100 and observations.get("p6_comprehensive_acceptance") != "PASS":
        return ProgressEvaluation("FAIL_CLOSED", None, phases, scores, ("p6_acceptance_required_for_100",))
    return ProgressEvaluation("VALID" if all(score is not None for score in scores.values()) else "UNKNOWN", overall, phases, scores, ())
