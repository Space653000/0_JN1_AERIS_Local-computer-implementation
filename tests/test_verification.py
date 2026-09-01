import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import verification


class VerificationGateTests(unittest.TestCase):
    def test_g4_rejects_executor_as_reviewer(self):
        with tempfile.TemporaryDirectory() as td, patch.object(verification, "VERIFICATION_ROOT", Path(td)), patch.object(verification, "load_task", return_value={"created_by": "Codex"}), patch.object(verification, "append_event"):
            with self.assertRaises(ValueError):
                verification.record_gate("T1", "G4_INDEPENDENT_REVIEW", "PASS", "Codex", evidence_refs=["review://1"], reviewer_role="independent_reviewer")
            result = verification.record_gate("T1", "G4_INDEPENDENT_REVIEW", "PASS", "Claude", evidence_refs=["review://1"], reviewer_role="independent_reviewer")
            self.assertEqual(result["gates"]["G4_INDEPENDENT_REVIEW"]["outcome"], "PASS")

    def test_g5_requires_human_chief_engineer(self):
        with tempfile.TemporaryDirectory() as td, patch.object(verification, "VERIFICATION_ROOT", Path(td)), patch.object(verification, "load_task", return_value={"created_by": "Codex"}), patch.object(verification, "append_event"):
            with self.assertRaises(ValueError):
                verification.record_gate("T2", "G5_APPROVAL", "PASS", "Claude", evidence_refs=["approval://1"], reviewer_role="independent_reviewer")
            result = verification.record_gate("T2", "G5_APPROVAL", "PASS", "Human", evidence_refs=["approval://1"], reviewer_role="Human Chief Engineer")
            self.assertEqual(result["gates"]["G5_APPROVAL"]["outcome"], "PASS")

    def test_pass_requires_evidence(self):
        with tempfile.TemporaryDirectory() as td, patch.object(verification, "VERIFICATION_ROOT", Path(td)), patch.object(verification, "load_task", return_value={"created_by": "Codex"}), patch.object(verification, "append_event"):
            with self.assertRaises(ValueError):
                verification.record_gate("T3", "G0_CONTRACT", "PASS", "tester")


if __name__ == "__main__":
    unittest.main()
