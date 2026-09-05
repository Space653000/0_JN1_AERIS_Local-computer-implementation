import copy
import unittest

from aeris_runtime.engineering import speaker_filter_realization, speaker_filter_realization_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_SPEAKER_BIQUAD_CROSSOVER",
    "sections": [{"b": [0.25, 0.5, 0.25], "a": [1.0, -0.5, 0.25]}],
    "coefficient_fractional_bits": 16, "maximum_pole_radius": 0.9,
    "maximum_coefficient_quantization_error": 0.0001,
    "lowpass_gain_at_crossover": 0.5, "highpass_gain_at_crossover": 0.5,
    "relative_phase_deg": 0.0, "maximum_phase_mismatch_deg": 10.0,
    "maximum_crossover_sum_deviation_db": 0.5, "input_peak_linear": 0.5,
    "section_peak_gains": [1.5], "available_output_peak_linear": 1.0,
    "group_delay_ms": 4.0, "maximum_group_delay_ms": 8.0,
}


class SpeakerFilterRealizationDomainTests(unittest.TestCase):
    def test_role_specific_poles_quantization_crossover_headroom_delay(self):
        result = speaker_filter_realization.analyze(BASE)
        self.assertEqual(len(result["pole_radii"]), 2)
        self.assertTrue(all(abs(radius - 0.5) < 1e-12 for radius in result["pole_radii"]))
        self.assertEqual(result["maximum_coefficient_quantization_error_actual"], 0.0)
        self.assertEqual(result["estimated_output_peak_linear"], 0.75)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["fixed_point_runtime_verified"])

    def test_phase_cancellation_and_unnormalized_section_fail_closed(self):
        result = speaker_filter_realization.analyze({**BASE, "relative_phase_deg": 180.0})
        checks = {row["id"]: row for row in result["checks"]}
        self.assertFalse(checks["CROSSOVER_SUM"]["passed"])
        self.assertFalse(checks["CROSSOVER_PHASE"]["passed"])
        with self.assertRaises(ValueError):
            speaker_filter_realization.analyze({**BASE, "sections": [{"b": [0.25, 0.5, 0.25], "a": [2.0, -0.5, 0.25]}]})
        with self.assertRaises(ValueError):
            speaker_filter_realization.analyze({**BASE, "section_peak_gains": []})

    def test_independent_review_rejects_runtime_claim(self):
        candidate = speaker_filter_realization.analyze(BASE)
        self.assertEqual(speaker_filter_realization_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate); wrong["fixed_point_runtime_verified"] = True
        rejected = speaker_filter_realization_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "fixed_point_runtime_verified")

    def test_r024_routes_to_exact_r005_filter_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R024", "speaker-filter-realization-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R005", "speaker-filter-realization-domain-review")["execution_passed"])
            result = run_role("R024", "speaker-filter-realization-baseline", BASE,
                              objective="Bound supplied biquad and crossover realization risks",
                              source_kind="SYNTHETIC")
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R005"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__": unittest.main()
