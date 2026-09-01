import tempfile
import unittest
from pathlib import Path
from unittest import mock

import aeris_runtime.watchdog as wd


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_state = wd.STATE_FILE
        wd.STATE_FILE = Path(self.tmp.name) / "state.json"

    def tearDown(self):
        wd.STATE_FILE = self.old_state
        self.tmp.cleanup()

    def test_healthy_service_is_not_restarted(self):
        start = mock.Mock(return_value={"started": True})
        report = wd.reconcile_once(
            status_fn=lambda port: {"reachable": True, "service_state": "SERVING"},
            start_fn=start,
        )
        self.assertEqual(report["state"], "HEALTHY")
        start.assert_not_called()

    @mock.patch("aeris_runtime.watchdog.append_event")
    def test_unreachable_service_is_recovered(self, _audit):
        states = iter([
            {"reachable": False},
            {"reachable": True, "service_state": "SERVING"},
        ])
        report = wd.reconcile_once(
            status_fn=lambda port: next(states),
            start_fn=lambda port: {"started": True, "pid": 123},
        )
        self.assertEqual(report["state"], "RECOVERED")
        self.assertEqual(report["action"], "SUPERVISOR_RESTARTED")

    @mock.patch("aeris_runtime.watchdog.append_event")
    def test_failed_restart_is_reported_not_bypassed(self, _audit):
        report = wd.reconcile_once(
            status_fn=lambda port: {"reachable": False, "error": "blocked"},
            start_fn=lambda port: {"started": False, "error": "opening blocked"},
        )
        self.assertEqual(report["state"], "BLOCKED_OR_FAILED")
        self.assertIn("NO_GATE_BYPASS", report["action"])


if __name__ == "__main__":
    unittest.main()
