import copy
import unittest

from aeris_runtime.engineering import speaker_bass_limiter, speaker_bass_limiter_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_BASS_LIMITER_ENVELOPE",
    "frequency_hz": [40.0, 60.0, 100.0],
    "requested_boost_db": [0.0, 3.0, 0.0],
    "baseline_peak_excursion_mm": [2.0, 1.5, 0.8],
    "maximum_peak_excursion_mm": 2.5,
    "excursion_relative_bound": 0.1,
    "predicted_coil_temperature_c": 92.0,
    "maximum_coil_temperature_c": 100.0,
    "temperature_bound_c": 5.0,
    "required_amplifier_peak_v": 8.0,
    "available_amplifier_peak_v": 10.0,
    "attack_ms": 2.0,
    "maximum_attack_ms": 3.0,
    "release_ms": 120.0,
    "minimum_release_ms": 80.0,
    "maximum_release_ms": 200.0,
    "content_crest_factor": 3.0,
    "minimum_crest_factor": 2.5,
}


class SpeakerBassLimiterDomainTests(unittest.TestCase):
    def test_role_specific_excursion_thermal_and_limiter_envelope(self):
        result = speaker_bass_limiter.analyze(BASE)
        self.assertAlmostEqual(result["boosted_peak_excursion_mm"][1], 1.5 * 10 ** (3 / 20))
        self.assertAlmostEqual(result["worst_excursion_upper_mm"], 1.5 * 10 ** (3 / 20) * 1.1)
        self.assertEqual(result["coil_temperature_upper_c"], 97.0)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["physical_measurement_verified"])

    def test_slow_attack_and_invalid_release_fail_closed(self):
        result = speaker_bass_limiter.analyze({**BASE, "attack_ms": 4.0})
        self.assertFalse({row["id"]: row for row in result["checks"]}["ATTACK_TIME"]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            speaker_bass_limiter.analyze({**BASE, "minimum_release_ms": 220.0})
        with self.assertRaises(ValueError):
            speaker_bass_limiter.analyze({**BASE, "frequency_hz": [40.0, 40.0, 100.0]})

    def test_independent_review_rejects_hidden_excursion(self):
        candidate = speaker_bass_limiter.analyze(BASE)
        self.assertEqual(speaker_bass_limiter_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate)
        wrong["worst_excursion_upper_mm"] = 1.0
        rejected = speaker_bass_limiter_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "worst_excursion_upper_mm")

    def test_r019_routes_to_exact_r025_protection_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R019", "speaker-bass-limiter-envelope-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R025", "speaker-bass-protection-domain-review")["execution_passed"])
            result = run_role(
                "R019", "speaker-bass-limiter-envelope-baseline", BASE,
                objective="Bound boost-derived excursion, thermal state and limiter timing without hiding alternatives",
                source_kind="SYNTHETIC",
            )
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R025"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
