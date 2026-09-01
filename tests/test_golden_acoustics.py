import json
import tempfile
import unittest
from pathlib import Path

from aeris_runtime import golden_acoustics


class GoldenAcousticTests(unittest.TestCase):
    def test_versioned_baseline_suite_passes(self):
        result = golden_acoustics.run_suite()
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["cases"], 5)
        self.assertEqual(result["passed"], 5)
        self.assertEqual(result["failed"], 0)
        self.assertIn("not a production-complete", result["truth"])

    def test_manifest_contains_positive_negative_and_input_integrity_cases(self):
        manifest = golden_acoustics.load_manifest()
        ids = {item["case_id"] for item in manifest["cases"]}
        self.assertIn("nominal-requirement-pass", ids)
        self.assertIn("regression-requirement-fail", ids)
        self.assertIn("duplicate-frequency-rejected", ids)
        for case in manifest["cases"]:
            self.assertEqual(len(case["sha256"]), 64)

    def test_tampered_input_hash_fails_closed(self):
        manifest = golden_acoustics.load_manifest()
        case = dict(manifest["cases"][0])
        case["sha256"] = "0" * 64
        result = golden_acoustics.run_case(case)
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["stage"], "INPUT_INTEGRITY")

    def test_manifest_duplicate_case_ids_are_rejected(self):
        manifest = golden_acoustics.load_manifest()
        bad = dict(manifest)
        bad["cases"] = [dict(manifest["cases"][0]), dict(manifest["cases"][0])]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(ValueError):
                golden_acoustics.load_manifest(path)


if __name__ == "__main__":
    unittest.main()
