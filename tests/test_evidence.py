import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import evidence


class EvidenceBundleTests(unittest.TestCase):
    def test_sealed_bundle_detects_tamper_and_extra_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "input.wav"
            source.write_bytes(b"RIFF-test")
            evroot = root / "evidence"
            with patch.object(evidence, "EVIDENCE_ROOT", evroot), patch.object(evidence, "append_event"):
                created = evidence.create_bundle("T1", "Codex", run_id="RUN1", input_paths=[source])
                self.assertEqual(created["run_id"], "RUN1")
                evidence.seal_bundle("RUN1", "Codex")
                self.assertTrue(evidence.validate_bundle("RUN1")["valid"])

                raw = evroot / "RUN1" / "raw" / "input.wav"
                raw.write_bytes(b"tampered")
                result = evidence.validate_bundle("RUN1")
                self.assertFalse(result["valid"])
                self.assertTrue(any("checksum mismatch" in item for item in result["errors"]))

    def test_unsealed_bundle_is_not_valid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "evidence"
            with patch.object(evidence, "EVIDENCE_ROOT", root), patch.object(evidence, "append_event"):
                evidence.create_bundle("T2", "Codex", run_id="RUN2")
                self.assertFalse(evidence.validate_bundle("RUN2")["valid"])


if __name__ == "__main__":
    unittest.main()
