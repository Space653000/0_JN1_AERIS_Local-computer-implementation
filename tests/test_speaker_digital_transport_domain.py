import copy
import unittest

from aeris_runtime.engineering import speaker_digital_transport, speaker_digital_transport_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "SUPPLIED_I2S_TDM_TRANSPORT", "sample_rate_hz": 48000.0,
    "slot_width_bits": 32, "word_length_bits": 24, "slots_per_frame": 2,
    "bit_clock_hz": 3072000.0, "bit_clock_relative_tolerance": 0.000001,
    "frame_sync_hz": 48000.0, "frame_sync_relative_tolerance": 0.000001,
    "buffer_capacity_frames": 256, "worst_case_service_interval_ms": 2.0,
    "minimum_buffer_margin_frames": 128, "maximum_buffer_latency_ms": 6.0,
    "expected_channel_count": 2, "active_slot_indices": [0, 1], "packing": "I2S_ONE_BIT_DELAY",
}


class SpeakerDigitalTransportDomainTests(unittest.TestCase):
    def test_role_specific_format_clock_slot_and_buffer_bounds(self):
        result = speaker_digital_transport.analyze(BASE)
        self.assertEqual(result["expected_bit_clock_hz"], 3072000.0)
        self.assertEqual(result["buffer_margin_frames"], 160.0)
        self.assertAlmostEqual(result["buffer_latency_ms"], 1000 * 256 / 48000)
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["glitch_free_playback_verified"])

    def test_clock_mismatch_and_duplicate_slot_fail_closed(self):
        result = speaker_digital_transport.analyze({**BASE, "bit_clock_hz": 3000000.0})
        self.assertFalse({row["id"]: row for row in result["checks"]}["BIT_CLOCK_RELATION"]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            speaker_digital_transport.analyze({**BASE, "active_slot_indices": [0, 0]})
        with self.assertRaises(ValueError):
            speaker_digital_transport.analyze({**BASE, "slot_width_bits": 32.0})

    def test_independent_review_rejects_physical_continuity_claim(self):
        candidate = speaker_digital_transport.analyze(BASE)
        self.assertEqual(speaker_digital_transport_review.review(BASE, candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
        wrong = copy.deepcopy(candidate); wrong["glitch_free_playback_verified"] = True
        rejected = speaker_digital_transport_review.review(BASE, wrong)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "glitch_free_playback_verified")

    def test_r014_routes_to_exact_r032_transport_qualification(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate("R014", "speaker-digital-transport-baseline")["execution_passed"])
            self.assertTrue(runner.evaluate("R032", "speaker-digital-transport-domain-review")["execution_passed"])
            result = run_role("R014", "speaker-digital-transport-baseline", BASE,
                              objective="Bound serial-audio format, clocks, slots and service buffer",
                              source_kind="SYNTHETIC")
            self.assertEqual(result["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in result["pod"]["reviewers"]], ["R032"])
            self.assertTrue(domain_review.review_status(result["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(result["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__": unittest.main()
