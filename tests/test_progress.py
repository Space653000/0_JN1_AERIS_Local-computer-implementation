import unittest

from aeris_runtime.progress import PHASES, _next_action


class NextActionTests(unittest.TestCase):
    def test_fail_closed_state_short_circuits(self):
        self.assertEqual(_next_action("FAIL_CLOSED", {p: 100 for p in PHASES}, []), {"kind": "fail_closed"})

    def test_all_phases_complete_reports_complete(self):
        items = [{"id": f"{p}.1", "state": "PASS"} for p in PHASES]
        self.assertEqual(_next_action("VALID", {p: 100 for p in PHASES}, items), {"kind": "complete"})

    def test_names_first_incomplete_phase_not_just_p0(self):
        # Regression: a prior version of this function only ever distinguished
        # "P0 incomplete" from "everything after P0", so it kept reporting a
        # stale P0-era message long after P1-P6 had real, unrelated progress.
        phase_percent = {"P0": 100, "P1": 100, "P2": 71, "P3": 75, "P4": 57, "P5": 33, "P6": 0}
        items = [{"id": "P2.1", "state": "PASS"}, {"id": "P2.3", "state": "UNKNOWN"}, {"id": "P2.4", "state": "UNKNOWN"}]
        result = _next_action("UNKNOWN", phase_percent, items)
        self.assertEqual(result, {"kind": "phase_pending", "phase": "P2", "pending_ids": ["P2.3", "P2.4"]})

    def test_skips_phases_already_at_100(self):
        phase_percent = {"P0": 100, "P1": 100, "P2": 100, "P3": 0, "P4": 0, "P5": 0, "P6": 0}
        items = [{"id": "P3.1", "state": "FAIL"}]
        result = _next_action("UNKNOWN", phase_percent, items)
        self.assertEqual(result["phase"], "P3")


if __name__ == "__main__":
    unittest.main()
