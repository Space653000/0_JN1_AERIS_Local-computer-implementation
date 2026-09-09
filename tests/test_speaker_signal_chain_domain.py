import copy
import unittest

from aeris_runtime.engineering import speaker_signal_chain, speaker_signal_chain_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_SPEAKER_SIGNAL_CHAIN",
    "stage_voltage_gains": [2.0, 5.0],
    "stage_input_noise_rms_v": [0.00001, 0.00002],
    "source_noise_rms_v": 0.000005,
    "source_signal_rms_v": 0.5,
    "source_impedance_ohm": 100.0,
    "chain_input_impedance_ohm": 10000.0,
    "minimum_loading_ratio": 20.0,
    "crest_factor": 2.0,
    "load_impedance_min_ohm": 4.0,
    "minimum_supported_load_ohm": 3.2,
    "available_output_peak_v": 12.0,
    "available_output_peak_a": 3.0,
    "maximum_output_noise_rms_v": 0.001,
    "noise_relative_bound": 0.1,
    "phase_margin_deg": 55.0,
    "minimum_phase_margin_deg": 45.0,
}


class SpeakerSignalChainDomainTests(unittest.TestCase):
    def test_role_specific_noise_gain_loading_and_headroom(self):
        result = speaker_signal_chain.analyze(BASE)
        self.assertEqual(result["total_voltage_gain"], 10.0)
        self.assertAlmostEqual(result["nominal_output_signal_rms_v"], 5.0)
        self.assertAlmostEqual(result["required_output_peak_v"], 10.0)
        self.assertAlmostEqual(result["required_output_peak_a"], 2.5)
        self.assertLess(result["output_noise_upper_rms_v"], 0.001)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["physical_measurement_verified"])

    def test_correlated_noise_and_unsupported_load_fail_closed(self):
        result = speaker_signal_chain.analyze({**BASE, "load_impedance_min_ohm": 3.0})
        self.assertFalse({row["id"]: row for row in result["checks"]}["LOAD_STABILITY"]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            speaker_signal_chain.analyze({**BASE, "noise_model": "CORRELATED"})
        with self.assertRaises(ValueError):
            speaker_signal_chain.analyze({**BASE, "stage_voltage_gains": [2.0], "stage_input_noise_rms_v": [1e-5, 2e-5]})

    def test_independent_review_rejects_hidden_current(self):
        candidate = speaker_signal_chain.analyze(BASE)
        self.assertEqual(speaker_signal_chain_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate)
        wrong["required_output_peak_a"] = 1.0
        rejected = speaker_signal_chain_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "required_output_peak_a")

    def test_r012_routes_to_exact_r013_headroom_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R012", "speaker-signal-chain-noise-headroom-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R013", "speaker-signal-chain-headroom-domain-review")["execution_passed"])
            result = run_role(
                "R012", "speaker-signal-chain-noise-headroom-baseline", BASE,
                objective="Bound speaker-chain referred noise, source loading and peak voltage/current headroom",
                source_kind="SYNTHETIC",
            )
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R013"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
