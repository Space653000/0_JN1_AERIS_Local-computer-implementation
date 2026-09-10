import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "progress_truth.v1.json"
AUTHORITY = "64576bdbe680170fc1ea27306d1a2ab494cac733"


class ProgressTruthContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_authority_is_canonical_blueprint(self):
        self.assertEqual(self.data["authority"]["blueprint_commit"], AUTHORITY)

    def test_required_item_count_is_54(self):
        items = [item for phase in self.data["required_items"].values() for item in phase]
        self.assertEqual(len(items), 54)
        self.assertEqual(len(set(items)), 54)

    def test_progress_is_fail_closed_without_evidence(self):
        policy = self.data["source_policy"]
        self.assertTrue(policy["machine_readable_required"])
        self.assertTrue(policy["chat_prose_is_not_evidence"])
        self.assertEqual(policy["missing_evidence_behavior"], "UNKNOWN")
        self.assertEqual(policy["conflicting_evidence_behavior"], "FAIL_CLOSED")

    def test_professional_validation_is_not_system_progress(self):
        self.assertTrue(self.data["source_policy"]["professional_validation_is_separate_metric"])

    def test_only_declared_evidence_scores_are_allowed(self):
        self.assertEqual(self.data["score_values"], [0, 20, 40, 60, 80, 90, 100])

    def test_provenance_fields_are_mandatory(self):
        required = set(self.data["provenance_required_fields"])
        self.assertEqual(required, {
            "authority_sha", "source_sha", "evidence_type",
            "evidence_pointer", "result", "observed_at"
        })

    def test_100_percent_requires_full_acceptance(self):
        rule = self.data["calculation"]["allow_100_only_when"]
        self.assertIn("all required item scores are 100", rule)
        self.assertIn("P6 comprehensive acceptance is PASS", rule)


if __name__ == "__main__":
    unittest.main()
