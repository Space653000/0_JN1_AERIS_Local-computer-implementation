import copy
import unittest

from aeris_runtime.engineering import speaker_tonal, speaker_tonal_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_SAMPLED_TONAL_EQ",
    "frequency_hz": [100, 500, 1000, 5000],
    "measured_level_db": [78, 80, 82, 79],
    "target_level_db": [80, 80, 80, 80],
    "spatial_spread_db": [1, 1, 1, 1],
    "level_uncertainty_db": 0.5,
    "maximum_boost_db": 3.5,
    "maximum_cut_db": 4.0,
    "available_headroom_db": 4.0,
    "headroom_reserve_db": 0.5,
    "smoothing_octaves": 1 / 6,
    "maximum_smoothing_octaves": 1 / 3,
    "unresolved_peak_db": 2.0,
    "maximum_unresolved_peak_db": 3.0,
    "room_notch_depth_db": 4.0,
    "maximum_boostable_notch_depth_db": 6.0,
    "loudness_match_error_db": 0.2,
    "maximum_loudness_match_error_db": 0.5,
    "normalization_mode": "ABSOLUTE_LEVEL_MATCHED",
}


class SpeakerTonalDomainTests(unittest.TestCase):
    def test_role_specific_correction_and_headroom_decision(self):
        result = speaker_tonal.analyze(BASE)
        self.assertEqual(result["proposed_correction_db"], [2, 0, -2, 1])
        self.assertEqual(result["boost_upper_db"], 3.5)
        self.assertEqual(result["cut_upper_db"], 3.5)
        self.assertEqual(result["required_headroom_db"], 4.0)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["listening_preference_verified"])
        self.assertFalse(result["physical_measurement_verified"])

    def test_deep_room_notch_and_peak_normalization_fail_closed(self):
        result = speaker_tonal.analyze({**BASE, "room_notch_depth_db": 8.0})
        self.assertFalse({row["id"]: row for row in result["checks"]}["ROOM_NOTCH_POLICY"]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            speaker_tonal.analyze({**BASE, "normalization_mode": "PEAK_NORMALIZED"})
        with self.assertRaises(ValueError):
            speaker_tonal.analyze({**BASE, "frequency_hz": [100, 100, 1000, 5000]})

    def test_independent_review_rejects_hidden_headroom(self):
        candidate = speaker_tonal.analyze(BASE)
        self.assertEqual(speaker_tonal_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate)
        wrong["required_headroom_db"] = 1.0
        rejected = speaker_tonal_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "required_headroom_db")

    def test_r018_routes_to_exact_r020_tonal_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R018", "speaker-tonal-eq-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R020", "speaker-tonal-context-domain-review")["execution_passed"])
            aggregate = runner.status("R020")
            self.assertEqual(aggregate["level"], "L2")
            self.assertEqual(aggregate["passed_capability_count"], 1)
            result = run_role(
                "R018", "speaker-tonal-eq-baseline", BASE,
                objective="Bound level-matched tonal correction without hiding headroom or room cancellation",
                source_kind="SYNTHETIC",
            )
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R020"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
