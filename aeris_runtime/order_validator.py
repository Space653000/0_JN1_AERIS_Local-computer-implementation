"""Validates ORDER.md handoff files from the independent Voice-Agent Front
Desk project and records the result as AERIS Evidence.

Two independent projects meet at exactly one integration point: a Markdown
file format (ORDER.md) dropped into a shared folder. This module is the
AERIS side of that boundary -- it does not execute the case, assemble a
pod, or produce a deliverable. It answers one question only: is this
ORDER.md well-formed enough to hand to the existing engineering/evidence
system (aeris_runtime.roles, aeris_runtime.engineering.orchestration)?

ORDER.md's `Selected Capability Pod` section is Front Desk's own guess at
which of the 100 roles should work the case -- it is not trusted as a
final assignment here. Every #NNN token in it is resolved through
aeris_runtime.roles.get_role(), the single canonical role registry, so a
hallucinated or out-of-range role number fails validation instead of being
silently recorded as fact. Confirming a role ID exists is not the same as
confirming that role can correctly solve the case; that judgment stays
with route_pod()/a human, not this validator.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import roles
from .audit import append_event
from .config import ROOT

# The brief's own suggested drop point between the two independent
# projects; it is not AERIS state, so it lives outside .aeris/ and outside
# the repo entirely. Overridable so tests never touch the real path.
HANDOFF_ORDERS_DIR = Path(os.environ.get("AERIS_HANDOFF_ORDERS_DIR", r"C:\0_JN1_AERIS_HANDOFF\orders"))
ORDER_EVIDENCE_DIR = ROOT / ".aeris" / "evidence" / "order"

REQUIRED_FRONTMATTER_FIELDS = (
    "case_id", "created_at", "input_mode", "language", "product", "project_phase", "priority", "status",
)
# Reuses the lifecycle vocabulary orchestration.route_pod() already
# requires, rather than inventing a second phase vocabulary. "unspecified"
# is accepted too: a voice conversation often can't extract this reliably,
# and Front Desk saying so honestly is exactly the disclosure AERIS wants
# over a guessed phase (confirmed against a real order Front Desk produced
# on 2026-09-16, which used exactly this value).
VALID_PROJECT_PHASES = (
    "Concept", "Architecture", "Prototype", "EVT", "DVT", "PVT", "MP", "Field", "Field Return", "unspecified",
)
REQUIRED_SECTIONS = (
    "User Goal", "Problem Type", "Known Symptoms", "Available Evidence", "Missing Evidence",
    "Constraints", "Selected Capability Pod", "Required Work", "Backend Required Deliverables",
    "Acceptance Criteria",
)
_SECTION_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
_ROLE_TOKEN_RE = re.compile(r"#(\d+)")


@dataclass(frozen=True)
class OrderValidation:
    state: str  # "VALID" | "FAIL_CLOSED"
    case_id: str | None
    order: dict[str, Any] | None
    pod_role_ids: tuple[str, ...]
    errors: tuple[str, ...]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a leading `---`-delimited flat key: value block from the body.

    Deliberately not a general YAML parser: ORDER.md's frontmatter is flat
    key: value pairs with no nesting or lists, and AERIS declares zero
    third-party dependencies (pyproject.toml) on purpose -- pulling in a
    full YAML library for this would be the first exception, for no real
    benefit. A malformed/missing frontmatter block returns ({}, text)
    rather than raising; validate_order's required-field check then
    reports each missing field individually, same as any other gap.
    """
    stripped = text.lstrip("\ufeff")
    lines = stripped.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    frontmatter: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip()
    return frontmatter, "\n".join(lines[end + 1:])


def parse_sections(body: str) -> dict[str, str]:
    """Split the Markdown body on heading lines into {heading: body_text}."""
    headings = list(_SECTION_HEADING_RE.finditer(body))
    sections: dict[str, str] = {}
    for i, match in enumerate(headings):
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        sections[match.group(1).strip()] = body[start:end].strip()
    return sections


def validate_order(text: str) -> OrderValidation:
    """Accumulate every schema problem before returning, the same
    fail-closed idiom progress_truth.evaluate_progress() uses: a human
    reading a rejected ORDER.md wants the full list of what is wrong, not
    one field at a time.
    """
    errors: list[str] = []
    frontmatter, body = parse_frontmatter(text)

    for field in REQUIRED_FRONTMATTER_FIELDS:
        if not frontmatter.get(field):
            errors.append(f"missing_frontmatter_field:{field}")

    project_phase = frontmatter.get("project_phase")
    if project_phase and project_phase not in VALID_PROJECT_PHASES:
        errors.append(f"invalid_project_phase:{project_phase}")

    sections = parse_sections(body)
    for section in REQUIRED_SECTIONS:
        if not sections.get(section, "").strip():
            errors.append(f"missing_section:{section}")

    pod_body = sections.get("Selected Capability Pod", "")
    tokens = list(dict.fromkeys(_ROLE_TOKEN_RE.findall(pod_body)))  # de-dup, preserve order
    if pod_body.strip() and not tokens:
        errors.append("no_role_ids_found_in_selected_capability_pod")
    pod_role_ids: list[str] = []
    for token in tokens:
        try:
            pod_role_ids.append(roles.get_role(token)["id"])
        except KeyError:
            errors.append(f"unknown_role_id:#{token}")

    order = {**frontmatter, "sections": sections}
    state = "VALID" if not errors else "FAIL_CLOSED"
    return OrderValidation(
        state=state,
        case_id=frontmatter.get("case_id") or None,
        order=order,
        pod_role_ids=tuple(pod_role_ids),
        errors=tuple(errors),
    )


def process_order(path: Path) -> dict[str, Any]:
    """Validate one ORDER.md, write AERIS Evidence for it, and log one
    audit event -- mirrors release_attestation.prepare_release_task()'s
    shape (do the work, log once at the end, return a plain summary dict).
    Re-running on the same case_id overwrites its Evidence file: an order
    is a living intake document that can legitimately move
    draft -> submitted, not a signed release attestation that must never
    change once written.
    """
    text = path.read_text(encoding="utf-8-sig")
    source_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    validation = validate_order(text)
    case_id = validation.case_id or path.stem

    ORDER_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_path = ORDER_EVIDENCE_DIR / f"{case_id}.json"
    evidence_path.write_text(json.dumps({
        "schema_version": 1,
        "case_id": case_id,
        "source_path": str(path),
        "source_sha256": source_sha256,
        "state": validation.state,
        "pod_role_ids": list(validation.pod_role_ids),
        "errors": list(validation.errors),
        "order": validation.order,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    append_event("ORDER_RECEIVED", "AERIS Order Validator", {
        "case_id": case_id, "source_path": str(path), "source_sha256": source_sha256,
        "result": validation.state, "errors": list(validation.errors),
    })

    return {
        "case_id": case_id, "state": validation.state, "errors": list(validation.errors),
        "pod_role_ids": list(validation.pod_role_ids), "evidence_path": str(evidence_path),
    }


def main() -> int:
    if len(sys.argv) > 1:
        paths = [Path(sys.argv[1])]
    else:
        HANDOFF_ORDERS_DIR.mkdir(parents=True, exist_ok=True)
        paths = sorted(HANDOFF_ORDERS_DIR.glob("*_ORDER.md"))

    if not paths:
        print(f"沒有找到任何 *_ORDER.md 檔案 / No *_ORDER.md files found in {HANDOFF_ORDERS_DIR}")
        return 0

    all_ok = True
    for path in paths:
        if not path.is_file():
            print(f"FAIL_CLOSED  {path}  不存在或不是檔案 / does not exist or is not a file")
            all_ok = False
            continue
        result = process_order(path)
        ok = result["state"] == "VALID"
        all_ok = all_ok and ok
        print(f"{'VALID' if ok else 'FAIL_CLOSED'}  {path.name}  case_id={result['case_id']}")
        if result["pod_role_ids"]:
            print("  Selected Capability Pod（僅供參考，非最終指派）"
                  f"/ (reference only, not a final assignment): {', '.join(result['pod_role_ids'])}")
        for err in result["errors"]:
            print(f"  - {err}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
