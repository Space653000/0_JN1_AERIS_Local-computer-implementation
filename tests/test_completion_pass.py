import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import completion
from aeris_runtime.completion import assess


class CompletionPassTests(unittest.TestCase):
    def test_report_has_required_autopilot_truth_fields(self):
        result=assess()
        for field in ("unresolved_software_gaps", "remaining_external_blockers", "remote_write_performed", "local_only_scope"):
            self.assertIn(field,result)
        self.assertFalse(result["remote_write_performed"])
        self.assertTrue(result["local_only_scope"])
        self.assertGreater(len(result["remaining_external_blockers"]),0)

    def test_declared_inventory_cannot_self_assert_complete(self):
        with patch.dict(completion.CHECKS, {"core_ui_ssot_six_pages": lambda: (False, "negative test")}, clear=False):
            result = assess()
        self.assertFalse(result["software_local_fixable_zero"])
        self.assertIn("core_ui_ssot_six_pages", {item["id"] for item in result["unresolved_software_gaps"]})

    def test_acceptance_rejects_previous_implementation(self):
        report = {
            "result": "PASS", "implementation_sha": "old",
            "checks": ["company_manifest", "unit_tests", "knowledge_build", "supported_machine_profile",
                       "core_cache_integrity", "local_doctor", "real_local_inference",
                       "offline_mode_doctor", "real_offline_mode_inference"],
        }
        with patch.object(completion, "_head_sha", return_value="current"), patch.object(completion, "_read", return_value=report):
            self.assertFalse(completion._acceptance()[0])
            report["implementation_sha"] = "current"
            self.assertTrue(completion._acceptance()[0])

    def test_browser_rejects_stale_commit_and_tampered_screenshot(self):
        temp_root = completion.ROOT / ".aeris" / "test-temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            artifact = Path(directory) / "screenshot.png"
            artifact.write_bytes(b"original screenshot")
            visual = {
                "AERIS_BROWSER_VISUAL_ACCESSIBILITY_BASELINE": "PASS", "implementation_sha": "current",
                "accessibility_markers_checked": 7,
                "routes": [{"artifact": str(artifact), "repeatable_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()} for _ in range(6)],
            }
            semantic = {"AERIS_BROWSER_LIVE_SEMANTIC_E2E": "PASS", "implementation_sha": "current", "routes": [{} for _ in range(6)]}
            monitor = {"result": "PASS", "implementation_sha": "current", "routes": 6, "checks": 360, "failure_count": 0}
            def read_report(path):
                return {"report.json": visual, "browser-semantic-live.json": semantic, "six-page-monitor.json": monitor}[path.name]
            with patch.object(completion, "_head_sha", return_value="current"), patch.object(completion, "_read", side_effect=read_report):
                self.assertTrue(completion._browser()[0])
                monitor["implementation_sha"] = "old"
                self.assertFalse(completion._browser()[0])
                monitor["implementation_sha"] = "current"
                artifact.write_bytes(b"changed screenshot")
                self.assertFalse(completion._browser()[0])

    def test_human_gate_does_not_hide_failed_software_baseline(self):
        with patch.dict(completion.GATE_CHECKS, {"full_methods_library": lambda: (False, "missing baseline")}, clear=False):
            result = assess()
        self.assertFalse(result["software_local_fixable_zero"])
        self.assertIn("full_methods_library:software_baseline", {item["id"] for item in result["unresolved_software_gaps"]})


if __name__ == "__main__": unittest.main()
