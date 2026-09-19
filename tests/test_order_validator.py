"""ORDER.md is the one integration point with an independent project (the
Voice-Agent Front Desk); nothing on the AERIS side reads it yet. These
tests lock in: the brief's own example validates cleanly end to end,
each required-field/section/role-id gap fails closed with a specific
error rather than a generic one, and process_order() writes Evidence and
an audit event without touching the real .aeris/ state."""
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import audit
from aeris_runtime import order_validator as ov
from aeris_runtime.config import ROOT

EXAMPLE_ORDER = """---
case_id: AERIS-20260915-180317
created_at: 2026-09-15T10:03:17+00:00
input_mode: voice
language: zh-TW
product: notebook
project_phase: DVT
priority: normal
status: draft
---

# User Goal
找出 NB Speaker 180-500 Hz SPL 比 Golden 低 4 dB 的主要原因

# Problem Type
Golden vs NG / Low-frequency SPL degradation

# Known Symptoms
- 180-500 Hz: -4 dB
- THD 增加
- 左右聲道皆有

# Available Evidence
- FR.csv
- THD.csv

# Missing Evidence
- Klippel nonlinear data

# Constraints
- 不修改 driver
- DVT 時程 3 天內

# Selected Capability Pod
- Lead: #041
- Micro Speaker Engineer: #018
- Enclosure Engineer: #021
- Reviewer: #003
- Final: #100

# Required Work
- Golden/NG FR 比較

# Backend Required Deliverables
- Results.xlsx
- Report.pptx

# Acceptance Criteria
- 所有結論需有 evidence
"""


class OrderValidatorSchemaTests(unittest.TestCase):
    """validate_order() is pure (no filesystem/audit side effects), so
    these run directly against the brief's own example text."""

    def test_example_order_from_brief_validates_clean(self):
        result = ov.validate_order(EXAMPLE_ORDER)
        self.assertEqual(result.state, "VALID")
        self.assertEqual(result.errors, ())
        self.assertEqual(result.case_id, "AERIS-20260915-180317")
        self.assertIn("R041", result.pod_role_ids)
        self.assertIn("R003", result.pod_role_ids)
        self.assertIn("R100", result.pod_role_ids)

    def test_missing_frontmatter_field_fails_closed(self):
        broken = EXAMPLE_ORDER.replace("case_id: AERIS-20260915-180317\n", "")
        result = ov.validate_order(broken)
        self.assertEqual(result.state, "FAIL_CLOSED")
        self.assertIn("missing_frontmatter_field:case_id", result.errors)

    def test_invalid_project_phase_fails_closed(self):
        broken = EXAMPLE_ORDER.replace("project_phase: DVT", "project_phase: Someday")
        result = ov.validate_order(broken)
        self.assertIn("invalid_project_phase:Someday", result.errors)

    def test_unspecified_project_phase_is_accepted_as_honest_disclosure(self):
        """A real order Front Desk produced on 2026-09-16 used this value
        when a voice conversation couldn't establish the phase -- that is
        an honest disclosure, not a guess, and should validate clean."""
        order = EXAMPLE_ORDER.replace("project_phase: DVT", "project_phase: unspecified")
        result = ov.validate_order(order)
        self.assertEqual(result.state, "VALID")

    def test_missing_section_fails_closed(self):
        broken = EXAMPLE_ORDER.replace(
            "# Constraints\n- 不修改 driver\n- DVT 時程 3 天內\n\n", "",
        )
        result = ov.validate_order(broken)
        self.assertEqual(result.state, "FAIL_CLOSED")
        self.assertIn("missing_section:Constraints", result.errors)

    def test_unknown_role_id_fails_closed_instead_of_being_trusted(self):
        """#141 is out of the real R001-R100 range -- Front Desk's pod
        guess must be checked against the real registry, never accepted
        as-is (see FRONTDESK_HANDOFF_BRIEF.md's own caveat about this)."""
        broken = EXAMPLE_ORDER.replace("Lead: #041", "Lead: #141")
        result = ov.validate_order(broken)
        self.assertEqual(result.state, "FAIL_CLOSED")
        self.assertIn("unknown_role_id:#141", result.errors)
        self.assertNotIn("R141", result.pod_role_ids)

    def test_no_leading_frontmatter_block_reports_every_missing_field(self):
        result = ov.validate_order("# User Goal\nsomething\n")
        self.assertEqual(result.state, "FAIL_CLOSED")
        for field in ov.REQUIRED_FRONTMATTER_FIELDS:
            self.assertIn(f"missing_frontmatter_field:{field}", result.errors)


class ProcessOrderTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        temp = ROOT / ".aeris/test-temp"
        temp.mkdir(parents=True, exist_ok=True)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(dir=temp)))
        self.stack.enter_context(patch.object(ov, "ORDER_EVIDENCE_DIR", root / "evidence"))
        self.stack.enter_context(patch.object(audit, "AUDIT_FILE", root / "audit.jsonl"))
        self.order_path = root / "AERIS-20260915-180317_ORDER.md"
        self.order_path.write_text(EXAMPLE_ORDER, encoding="utf-8")

    def test_writes_evidence_file_and_one_audit_event(self):
        result = ov.process_order(self.order_path)
        self.assertEqual(result["state"], "VALID")
        self.assertEqual(result["case_id"], "AERIS-20260915-180317")

        evidence_path = Path(result["evidence_path"])
        self.assertTrue(evidence_path.is_file())
        record = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(record["state"], "VALID")
        self.assertEqual(record["case_id"], "AERIS-20260915-180317")
        self.assertIn("R041", record["pod_role_ids"])

        ledger_lines = audit.AUDIT_FILE.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(ledger_lines), 1)
        event = json.loads(ledger_lines[0])
        self.assertEqual(event["event_type"], "ORDER_RECEIVED")
        self.assertEqual(event["payload"]["case_id"], "AERIS-20260915-180317")
        self.assertEqual(event["payload"]["result"], "VALID")

    def test_revalidating_same_case_id_overwrites_not_duplicates(self):
        ov.process_order(self.order_path)
        ov.process_order(self.order_path)
        evidence_files = list((ov.ORDER_EVIDENCE_DIR).glob("*.json"))
        self.assertEqual(len(evidence_files), 1)


if __name__ == "__main__":
    unittest.main()
