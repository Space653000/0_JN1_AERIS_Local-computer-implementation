import copy
import unittest

from aeris_runtime.engineering import structural_acoustic, structural_acoustic_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_STRUCTURAL_ACOUSTIC_BANDS",
    "frequency_hz": [100.0, 200.0, 400.0],
    "acceleration_rms_m_s2": [0.2, 0.4, 0.1],
    "pressure_rms_pa": [0.02, 0.08, 0.005],
    "coherence": [0.8, 0.95, 0.3],
    "acceleration_noise_floor_m_s2": [0.01, 0.01, 0.01],
    "pressure_noise_floor_pa": [0.001, 0.001, 0.001],
    "minimum_acceleration_snr_ratio": 5.0,
    "minimum_pressure_snr_ratio": 5.0,
    "minimum_coherence": 0.7,
    "minimum_identifiable_band_fraction": 0.6,
    "maximum_transfer_spread_ratio": 2.5,
    "frequency_alignment_bound_hz": 1.0,
    "maximum_frequency_alignment_bound_hz": 2.0,
}


class StructuralAcousticDomainTests(unittest.TestCase):
    def test_role_specific_transfer_identifiability(self):
        result = structural_acoustic.analyze(BASE)
        self.assertEqual(result["identifiable_band_indices"], [0, 1])
        for actual, expected in zip(result["transfer_pa_per_m_s2"], [0.1, 0.2, 0.05]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(result["identifiable_band_fraction"], 2 / 3)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["causal_path_verified"])

    def test_low_coherence_and_bad_units_fail_closed(self):
        result = structural_acoustic.analyze({**BASE, "coherence": [0.2, 0.3, 0.1]})
        self.assertFalse({row["id"]: row for row in result["checks"]}["IDENTIFIABLE_BAND_FRACTION"]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            structural_acoustic.analyze({**BASE, "pressure_rms_db_spl": [60, 70, 50]})
        with self.assertRaises(ValueError):
            structural_acoustic.analyze({**BASE, "coherence": [0.8, 1.1, 0.3]})

    def test_independent_review_rejects_causal_overclaim(self):
        candidate = structural_acoustic.analyze(BASE)
        self.assertEqual(structural_acoustic_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate)
        wrong["causal_path_verified"] = True
        rejected = structural_acoustic_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "causal_path_verified")

    def test_r022_routes_to_exact_r073_path_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R022", "structural-acoustic-transfer-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R073", "structural-acoustic-path-domain-review")["execution_passed"])
            result = run_role(
                "R022", "structural-acoustic-transfer-baseline", BASE,
                objective="Separate identifiable structural/acoustic transfer from unsupported causal claims",
                source_kind="SYNTHETIC",
            )
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R073"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
