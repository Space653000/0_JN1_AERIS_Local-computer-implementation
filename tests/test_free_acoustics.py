import math
import unittest

from aeris_runtime.free_acoustics import analyze
from aeris_runtime.skills_runtime import run_skill


class FreeAcousticBaselineTests(unittest.TestCase):
    def _tone(self, frequency=1000.0, rate=8000.0, count=1024):
        return [math.sin(2 * math.pi * frequency * i / rate) for i in range(count)]

    def test_full_free_baseline_capability_surface(self):
        tone = self._tone()
        result = run_skill("free-local-acoustic-baseline", {
            "samples": tone, "reference_samples": tone, "sample_rate_hz": 8000,
            "input_kind": "impulse_response",
            "fundamental_hz": 1000, "octave_fraction": 3,
            "filter_type": "lowpass", "filter_cutoff_hz": 1500,
            "calibration_pa_per_unit": 1,
        })
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["capability_maturity"], "FREE_BASELINE")
        self.assertEqual(result["professional_verification"], "NOT_CLAIMED")
        for field in ("fft", "frequency_response", "thd_percent", "snr_db", "spl_db_re_20upa", "impulse_response", "octave_bands", "filtered_samples", "transfer_function", "stft", "coherence", "deterministic_plot_svg", "report"):
            self.assertIn(field, result)
        self.assertAlmostEqual(result["fft"]["peak_hz"], 1000.0, delta=8.0)

    def test_negative_non_finite_and_bad_calibration_fail_closed(self):
        with self.assertRaises(ValueError):
            analyze({"samples": [0.0] * 7 + [float("nan")], "sample_rate_hz": 8000})
        with self.assertRaises(ValueError):
            analyze({"samples": [0.0] * 16, "sample_rate_hz": 8000, "calibration_pa_per_unit": 0})
        with self.assertRaises(ValueError):
            analyze({"samples": [0.0] * 16, "sample_rate_hz": 8000, "input_kind": "guessed_ir"})


if __name__ == "__main__":
    unittest.main()
