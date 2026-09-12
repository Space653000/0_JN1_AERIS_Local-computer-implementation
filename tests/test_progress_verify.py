"""P2.6: the Progress Engine's own generator must be trustworthy, not just the
consumer-side fail-closed evaluator it feeds."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import progress_verify


class ProgressVerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_forced_failure_is_not_reported_as_pass_and_is_removed_from_truth(self):
        truth_path = self.tmp / "PROGRESS_TRUTH.json"
        truth_path.write_text(json.dumps({"schema_version": 1, "items": {
            "P1.1": {"result": "PASS", "score": 100, "source_sha": "stale"},
        }}), encoding="utf-8")
        failing = progress_verify.CheckResult(False, "deliberately broken for this test", "nowhere")
        with patch.object(progress_verify, "EVIDENCE_DIR", self.tmp), \
             patch.object(progress_verify, "TRUTH_PATH", truth_path), \
             patch.object(progress_verify, "CHECKS", {"P1.1": lambda: failing}), \
             patch.object(progress_verify, "_head_sha", return_value="deadbeef"):
            report = progress_verify.run(["P1.1"], write=True)
        self.assertEqual(report["P1.1"]["result"], "FAIL")
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        self.assertNotIn("P1.1", truth["items"], "a failed re-check must not leave the previous PASS claim standing")

    def test_passing_check_writes_schema_correct_evidence_and_truth_entry(self):
        truth_path = self.tmp / "PROGRESS_TRUTH.json"
        passing = progress_verify.CheckResult(True, "everything checked out", "some/artifact.py")
        with patch.object(progress_verify, "EVIDENCE_DIR", self.tmp), \
             patch.object(progress_verify, "TRUTH_PATH", truth_path), \
             patch.object(progress_verify, "CHECKS", {"P1.1": lambda: passing}), \
             patch.object(progress_verify, "_head_sha", return_value="cafef00d"):
            report = progress_verify.run(["P1.1"], write=True)
        self.assertEqual(report["P1.1"]["result"], "PASS")
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        record = truth["items"]["P1.1"]
        for field in ("authority_sha", "source_sha", "evidence_type", "evidence_pointer", "result", "observed_at"):
            self.assertIn(field, record)
        self.assertEqual(record["source_sha"], "cafef00d")
        evidence_files = list(self.tmp.glob("P1.1-PASS-*.json"))
        self.assertEqual(len(evidence_files), 1)
        evidence = json.loads(evidence_files[0].read_text(encoding="utf-8"))
        self.assertEqual(evidence["candidate_sha"], "cafef00d")
        self.assertEqual(evidence["relevant_output"], ["everything checked out"])

    def test_unregistered_item_is_unknown_not_a_guessed_pass(self):
        report = progress_verify.run(["P9.9-does-not-exist"], write=False)
        self.assertEqual(report["P9.9-does-not-exist"]["result"], "UNKNOWN")

    def test_dry_run_writes_nothing(self):
        truth_path = self.tmp / "PROGRESS_TRUTH.json"
        passing = progress_verify.CheckResult(True, "ok", "artifact")
        with patch.object(progress_verify, "EVIDENCE_DIR", self.tmp), \
             patch.object(progress_verify, "TRUTH_PATH", truth_path), \
             patch.object(progress_verify, "CHECKS", {"P1.1": lambda: passing}), \
             patch.object(progress_verify, "_head_sha", return_value="cafef00d"):
            progress_verify.run(["P1.1"], write=False)
        self.assertFalse(truth_path.exists())
        self.assertEqual(list(self.tmp.glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
