import copy
import unittest

from aeris_runtime.engineering import room_correction, room_correction_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_MULTI_POSITION_ROOM_CORRECTION",
    "frequency_hz": [100.0, 500.0, 2000.0],
    "position_response_db": [[-2.0, 1.0, 0.0], [-1.0, 0.0, 1.0], [-3.0, 0.5, -1.0]],
    "target_response_db": [0.0, 0.0, 0.0],
    "response_uncertainty_db": 0.5,
    "minimum_position_count": 3,
    "maximum_spatial_spread_db": 3.0,
    "maximum_boost_db": 3.5,
    "maximum_cut_db": 3.0,
    "deep_notch_depth_db": 5.0,
    "maximum_boostable_notch_depth_db": 6.0,
    "required_filter_latency_ms": 8.0,
    "maximum_filter_latency_ms": 10.0,
    "nonminimum_phase_band_count": 0,
    "maximum_nonminimum_phase_band_count": 0,
}


class RoomCorrectionDomainTests(unittest.TestCase):
    def test_role_specific_spatial_correction_envelope(self):
        result = room_correction.analyze(BASE)
        self.assertEqual(result["mean_response_db"], [-2.0, 0.5, 0.0])
        self.assertEqual(result["proposed_correction_db"], [2.0, -0.5, 0.0])
        self.assertEqual(result["maximum_spatial_spread_db"], 2.0)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["realized_filter_verified"])

    def test_position_specific_notch_and_shape_fail_closed(self):
        result = room_correction.analyze({**BASE, "deep_notch_depth_db": 8.0})
        self.assertFalse({row["id"]: row for row in result["checks"]}["DEEP_NOTCH_POLICY"]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            room_correction.analyze({**BASE, "position_response_db": [[-2.0, 1.0], [-1.0, 0.0, 1.0]]})
        with self.assertRaises(ValueError):
            room_correction.analyze({**BASE, "frequency_hz": [100.0, 100.0, 2000.0]})

    def test_independent_review_rejects_realized_filter_claim(self):
        candidate = room_correction.analyze(BASE)
        self.assertEqual(room_correction_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate)
        wrong["realized_filter_verified"] = True
        rejected = room_correction_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "realized_filter_verified")

    def test_r026_routes_to_exact_r071_spatial_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R026", "room-correction-spatial-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R071", "room-correction-spatial-domain-review")["execution_passed"])
            result = run_role("R026", "room-correction-spatial-baseline", BASE,
                              objective="Bound multi-position correction without claiming a realized filter",
                              source_kind="SYNTHETIC")
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R071"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
