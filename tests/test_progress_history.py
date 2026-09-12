"""P2.3: progress history must be reconstructed from real, timestamped
per-item Evidence files -- never estimated or fabricated."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import progress_history


class ProgressHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _write(self, name, item, result, sha, captured):
        (self.tmp / name).write_text(json.dumps({
            "item": item, "result": result, "candidate_sha": sha, "captured_at_utc": captured,
        }), encoding="utf-8")

    def test_empty_evidence_dir_returns_empty_list(self):
        with patch.object(progress_history, "load_contract", return_value={"required_items": {"P0": ["P0.1"]}}):
            self.assertEqual(progress_history.compute_history(self.tmp), [])

    def test_reconstructs_chronological_percent_from_real_evidence(self):
        self._write("a.json", "P0.1", "PASS", "sha1", "2026-01-01T00:00:00Z")
        self._write("b.json", "P0.2", "FAIL", "sha1", "2026-01-01T00:00:01Z")
        self._write("c.json", "P0.1", "PASS", "sha2", "2026-01-02T00:00:00Z")
        self._write("d.json", "P0.2", "PASS", "sha2", "2026-01-02T00:00:01Z")
        contract = {"required_items": {"P0": ["P0.1", "P0.2"]}}
        with patch.object(progress_history, "load_contract", return_value=contract):
            points = progress_history.compute_history(self.tmp)
        self.assertEqual([p["candidate_sha"] for p in points], ["sha1", "sha2"])
        self.assertEqual(points[0]["overall_percent"], 50)
        self.assertEqual(points[1]["overall_percent"], 100)
        self.assertEqual(points, sorted(points, key=lambda p: p["captured_at_utc"]))

    def test_only_latest_capture_per_item_per_sha_is_used(self):
        self._write("old.json", "P0.1", "FAIL", "sha1", "2026-01-01T00:00:00Z")
        self._write("new.json", "P0.1", "PASS", "sha1", "2026-01-01T00:00:05Z")
        contract = {"required_items": {"P0": ["P0.1"]}}
        with patch.object(progress_history, "load_contract", return_value=contract):
            points = progress_history.compute_history(self.tmp)
        self.assertEqual(points[0]["overall_percent"], 100)

    def test_malformed_json_file_is_skipped_not_fatal(self):
        (self.tmp / "broken.json").write_text("{not json", encoding="utf-8")
        self._write("ok.json", "P0.1", "PASS", "sha1", "2026-01-01T00:00:00Z")
        contract = {"required_items": {"P0": ["P0.1"]}}
        with patch.object(progress_history, "load_contract", return_value=contract):
            points = progress_history.compute_history(self.tmp)
        self.assertEqual(len(points), 1)

    def test_unreadable_contract_fails_closed_to_empty_list(self):
        self._write("ok.json", "P0.1", "PASS", "sha1", "2026-01-01T00:00:00Z")
        with patch.object(progress_history, "load_contract", side_effect=ValueError("boom")):
            self.assertEqual(progress_history.compute_history(self.tmp), [])


if __name__ == "__main__":
    unittest.main()
