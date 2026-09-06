import copy
import unittest

from aeris_runtime.engineering import room_decay, room_decay_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_ROOM_DECAY_POSITION_FITS",
    "frequency_band_hz": 500.0,
    "position_ids": ["front", "center", "rear"],
    "decay_rate_db_per_s": [40.0, 30.0, 20.0],
    "fit_span_db": [35.0, 30.0, 20.0],
    "noise_margin_db": [12.0, 8.0, 3.0],
    "fit_r_squared": [0.98, 0.95, 0.8],
    "minimum_fit_span_db": 25.0,
    "minimum_noise_margin_db": 6.0,
    "minimum_fit_r_squared": 0.9,
    "minimum_valid_position_fraction": 2 / 3,
    "maximum_valid_rt60_s": 2.5,
    "maximum_valid_rt60_spread_s": 1.0,
    "window_duration_s": 2.2,
    "minimum_window_duration_s": 2.0,
}


class RoomDecayDomainTests(unittest.TestCase):
    def test_role_specific_position_decay_fit_screen(self):
        result = room_decay.analyze(BASE)
        self.assertEqual(result["rt60_s"], [1.5, 2.0, 3.0])
        self.assertEqual(result["valid_position_ids"], ["front", "center"])
        self.assertAlmostEqual(result["valid_position_fraction"], 2 / 3)
        self.assertEqual(result["valid_rt60_spread_s"], 0.5)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["diffuse_field_verified"])

    def test_noise_floor_and_invalid_decay_rate_fail_closed(self):
        result = room_decay.analyze({**BASE, "noise_margin_db": [2.0, 2.0, 2.0]})
        self.assertFalse({row["id"]: row for row in result["checks"]}["VALID_POSITION_COVERAGE"]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            room_decay.analyze({**BASE, "decay_rate_db_per_s": [40.0, -30.0, 20.0]})
        with self.assertRaises(ValueError):
            room_decay.analyze({**BASE, "position_ids": ["front", "front", "rear"]})

    def test_independent_review_rejects_diffuse_field_overclaim(self):
        candidate = room_decay.analyze(BASE)
        self.assertEqual(room_decay_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate)
        wrong["diffuse_field_verified"] = True
        rejected = room_decay_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "diffuse_field_verified")

    def test_r023_routes_to_exact_r072_room_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R023", "room-decay-spatial-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R072", "room-decay-spatial-domain-review")["execution_passed"])
            result = run_role(
                "R023", "room-decay-spatial-baseline", BASE,
                objective="Bound multi-position decay fits without claiming a diffuse field",
                source_kind="SYNTHETIC",
            )
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R072"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
