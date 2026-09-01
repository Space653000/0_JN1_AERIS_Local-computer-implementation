import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from aeris_runtime import operations


class OperationsTests(unittest.TestCase):
    def _patch_common(self, td: str, *, core_valid=True, supported=True, local_ok=True, acceptance=None, unverified=None):
        state = Path(td) / "state"
        state.mkdir(parents=True, exist_ok=True)
        maturity = Path(td) / "maturity.json"
        maturity.write_text('{"capabilities":{}}', encoding="utf-8")
        router = MagicMock()
        router.local.health.return_value = (local_ok, "test")
        return [
            patch.object(operations, "STATE_DIR", state),
            patch.object(operations, "OPENING_FILE", state / "COMPANY_OPENING.json"),
            patch.object(operations, "HEARTBEAT_FILE", state / "HEARTBEAT.json"),
            patch.object(operations, "ACCEPTANCE_FILE", state / "LOCAL_ACCEPTANCE.json"),
            patch.object(operations, "MATURITY_FILE", maturity),
            patch.object(operations, "load_config", return_value=SimpleNamespace(mode="auto", local_network_scope="loopback", local_model="test-model")),
            patch.object(operations, "validate_company_manifest", return_value=SimpleNamespace(valid=True)),
            patch.object(operations, "machine_detect", return_value={"profile": "test", "supported_baseline": supported}),
            patch.object(operations, "verify_core_cache", return_value={"valid": core_valid, "mode": "test"}),
            patch.object(operations, "ModelRouter", return_value=router),
            patch.object(operations, "verify_ledger", return_value={"valid": True, "records": 0}),
            patch.object(operations, "_unverified_capabilities", return_value=unverified if unverified is not None else []),
            patch.object(operations, "_read_json", side_effect=lambda path: acceptance if Path(path).name == "LOCAL_ACCEPTANCE.json" else None),
        ]

    def test_core_failure_blocks_opening(self):
        with tempfile.TemporaryDirectory() as td:
            patches = self._patch_common(td, core_valid=False)
            for p in patches: p.start()
            try:
                result = operations.assess_opening()
                self.assertEqual(result["operational_state"], "BLOCKED")
                self.assertIn("CORE_CACHE_NOT_VERIFIED", result["blockers"])
            finally:
                for p in reversed(patches): p.stop()

    def test_no_acceptance_is_open_with_limits_not_verified(self):
        with tempfile.TemporaryDirectory() as td:
            patches = self._patch_common(td, acceptance=None)
            for p in patches: p.start()
            try:
                result = operations.assess_opening()
                self.assertEqual(result["operational_state"], "OPEN_WITH_LIMITS")
                self.assertIsNone(result["verified_scope"])
                self.assertIn("REAL_MACHINE_ACCEPTANCE_NOT_RUN", result["limits"])
            finally:
                for p in reversed(patches): p.stop()

    def test_passed_acceptance_opens_only_kernel_scope(self):
        acceptance = {"result": "PASS", "hard_offline_network_state": "NOT_TESTED"}
        with tempfile.TemporaryDirectory() as td:
            patches = self._patch_common(td, acceptance=acceptance, unverified=[{"capability": "skills_library", "state": "NOT_IMPLEMENTED"}])
            for p in patches: p.start()
            try:
                result = operations.assess_opening()
                self.assertEqual(result["operational_state"], "OPEN_VERIFIED_SCOPE")
                self.assertEqual(result["verified_scope"], "LOCAL_PORTABLE_COMPANY_KERNEL_BASELINE")
                self.assertFalse(result["company_complete"])
                self.assertIn("PROFESSIONAL_ACOUSTIC_CAPABILITIES_REMAIN_UNVERIFIED_OR_INCOMPLETE", result["limits"])
            finally:
                for p in reversed(patches): p.stop()

    def test_open_company_records_real_expected_run_result(self):
        acceptance = {"result": "PASS", "hard_offline_network_state": "NOT_TESTED"}
        with tempfile.TemporaryDirectory() as td:
            patches = self._patch_common(td, acceptance=acceptance)
            for p in patches: p.start()
            try:
                with patch.object(operations, "ensure_expected_runs") as ensure, patch.object(operations, "mark_expected_run") as mark, patch.object(operations, "append_event"):
                    result = operations.open_company("test-actor")
                    self.assertEqual(result["operational_state"], "OPEN_VERIFIED_SCOPE")
                    self.assertTrue(operations.OPENING_FILE.is_file())
                    ensure.assert_called_once_with(actor="test-actor")
                    mark.assert_called_once_with("company-opening-assessment", True, error="", actor="test-actor")
            finally:
                for p in reversed(patches): p.stop()

    def test_heartbeat_updates_expected_run_without_audit_spam(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state"
            state.mkdir()
            with patch.object(operations, "STATE_DIR", state), patch.object(operations, "HEARTBEAT_FILE", state / "HEARTBEAT.json"), patch.object(operations, "mark_expected_run") as mark:
                operations._write_heartbeat(8765, {"operational_state": "OPEN_VERIFIED_SCOPE"})
                self.assertTrue((state / "HEARTBEAT.json").is_file())
                mark.assert_called_once_with("supervisor-heartbeat", True, actor="AERIS Supervisor", audit_event=False)

    def test_supervisor_is_hard_bound_to_loopback(self):
        self.assertEqual(operations.DEFAULT_HOST, "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
