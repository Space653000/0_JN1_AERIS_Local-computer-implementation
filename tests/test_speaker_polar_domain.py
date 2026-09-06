import copy
import unittest

from aeris_runtime.engineering import speaker_polar, speaker_polar_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_HORIZONTAL_POLAR_ABSOLUTE",
    "angles_deg": [-90, -60, -30, 0, 30, 60, 90],
    "levels_db": [70, 76, 79, 80, 79, 76, 70],
    "supplied_on_axis_reference_db": 80,
    "level_uncertainty_db": 0.5,
    "minimum_coverage_deg": 180,
    "maximum_angular_gap_deg": 30,
    "maximum_on_axis_reference_error_db": 1,
    "minimum_edge_attenuation_db": 8,
    "maximum_symmetry_error_db": 1,
    "angle_alignment_bound_deg": 1,
    "maximum_angle_alignment_bound_deg": 2,
    "normalization_mode": "ABSOLUTE_NOT_PEAK_NORMALIZED",
}


class SpeakerPolarDomainTests(unittest.TestCase):
    def test_absolute_sampled_polar_decision(self):
        result = speaker_polar.analyze(BASE)
        self.assertEqual(result["coverage_deg"], 180)
        self.assertEqual(result["maximum_gap_deg"], 30)
        self.assertEqual(result["on_axis_level_db"], 80)
        self.assertEqual(result["edge_attenuation_db"], [10, 10])
        self.assertEqual(result["maximum_symmetry_error_db"], 0)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["continuous_angle_verified"])
        self.assertFalse(result["physical_measurement_verified"])

    def test_sparse_or_peak_normalized_inputs_fail_closed(self):
        sparse = {**BASE, "angles_deg": [-90, 0, 90], "levels_db": [70, 80, 70]}
        result = speaker_polar.analyze(sparse)
        self.assertFalse(result["checks"][1]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            speaker_polar.analyze({**BASE, "normalization_mode": "PEAK_NORMALIZED"})
        with self.assertRaises(ValueError):
            speaker_polar.analyze({**BASE, "angles_deg": [-90, -30, 0, 30], "levels_db": [70, 79, 80, 79]})

    def test_independent_reviewer_rejects_hidden_asymmetry(self):
        candidate = speaker_polar.analyze(BASE)
        self.assertEqual(speaker_polar_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate)
        wrong["maximum_symmetry_error_db"] = 0.8
        rejected = speaker_polar_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "maximum_symmetry_error_db")

    def test_r017_routes_to_exact_second_r034_spatial_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R017", "speaker-polar-spatial-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R034", "speaker-polar-spatial-domain-review")["execution_passed"])
            aggregate = runner.status("R034")
            self.assertEqual(aggregate["level"], "L1")
            self.assertEqual(aggregate["passed_capability_count"], 1)
            result = run_role(
                "R017", "speaker-polar-spatial-baseline", BASE,
                objective="Bound absolute sampled speaker directivity without hiding off-axis loss",
                source_kind="SYNTHETIC",
            )
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R034"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
