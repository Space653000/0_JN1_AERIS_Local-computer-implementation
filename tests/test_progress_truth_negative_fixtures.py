import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "progress_truth.v1.json"
AUTHORITY = "64576bdbe680170fc1ea27306d1a2ab494cac733"


def validate_evidence(contract, evidence):
    required = set(contract["provenance_required_fields"])
    missing = sorted(required - set(evidence))
    if missing:
        return "UNKNOWN", f"missing provenance: {','.join(missing)}"
    if evidence["authority_sha"] != AUTHORITY:
        return "FAIL_CLOSED", "authority mismatch"
    if evidence["result"] not in {"PASS", "FAIL", "BLOCKED_EXTERNAL", "NOT_VERIFIED"}:
        return "FAIL_CLOSED", "invalid result"
    return "ACCEPTED", "provenance complete"


class ProgressTruthNegativeFixtureTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.good = {
            "authority_sha": AUTHORITY,
            "source_sha": "44c0e507b305a6708cd80b6be43a82e314959c0d",
            "evidence_type": "ci",
            "evidence_pointer": "run:34428559347",
            "result": "PASS",
            "observed_at": "2026-09-10T12:44:00+08:00",
        }

    def test_complete_provenance_is_accepted(self):
        self.assertEqual(validate_evidence(self.contract, self.good)[0], "ACCEPTED")

    def test_missing_each_required_field_never_becomes_progress(self):
        for field in self.contract["provenance_required_fields"]:
            with self.subTest(field=field):
                broken = copy.deepcopy(self.good)
                broken.pop(field)
                self.assertEqual(validate_evidence(self.contract, broken)[0], "UNKNOWN")

    def test_wrong_blueprint_authority_fails_closed(self):
        broken = copy.deepcopy(self.good)
        broken["authority_sha"] = "0" * 40
        self.assertEqual(validate_evidence(self.contract, broken)[0], "FAIL_CLOSED")

    def test_unrecognized_result_fails_closed(self):
        broken = copy.deepcopy(self.good)
        broken["result"] = "TRUST_ME"
        self.assertEqual(validate_evidence(self.contract, broken)[0], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
