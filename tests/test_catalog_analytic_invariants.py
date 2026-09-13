"""P5.4-adjacent: broaden regression coverage for shared-catalog skills
across multiple points in their input space, without touching the
single-fixture-per-skill contract in cases.py/catalog.py (see
docs/AERIS_P5_ENGINEER_FACTORY.md's P5.4 section for why that contract is
not safely extensible in a single tick). Each skill's existing
golden/engineering/*/*/golden.json checks exactly one analytic point;
these tests independently re-derive the same physical formula and check
it holds at several other points, catching a regression that a single
fixed point could miss (e.g. a sign error that only shows up off a
convenient round number)."""
import math
import unittest

from aeris_runtime.engineering import catalog


class ButterworthUnitDcGainTests(unittest.TestCase):
    """A stable unity-DC-gain lowpass filter's impulse response must sum
    to 1 regardless of cutoff/order -- this is a property of the filter
    design, not a coincidence of one fixture's numbers."""

    def _impulse_sum(self, cutoff_hz, order):
        samples = [0.0] * 512
        samples[0] = 1.0
        params = {"samples": samples, "sample_rate_hz": 8192, "cutoff_hz": [cutoff_hz], "order": order, "kind": "lowpass"}
        result = catalog.execute("butterworth-filter", params)
        return sum(result["values"]["filtered_samples"])

    def test_dc_gain_holds_across_cutoffs_and_orders(self):
        for cutoff_hz, order in [(256, 2), (1024, 6), (2000, 8), (512, 4)]:
            with self.subTest(cutoff_hz=cutoff_hz, order=order):
                self.assertAlmostEqual(self._impulse_sum(cutoff_hz, order), 1.0, places=6)


class LumpedSpeakerResonanceTests(unittest.TestCase):
    """fs = 1 / (2*pi*sqrt(Mms*Cms)) at resonance -- independently
    re-derived here and checked against several mass/compliance pairs,
    not just the one pair the shared golden fixture already covers."""

    def _fs_hz(self, moving_mass_kg, compliance_m_per_n):
        params = {
            "moving_mass_kg": moving_mass_kg, "compliance_m_per_n": compliance_m_per_n,
            "mechanical_resistance_ns_per_m": 1, "force_factor_n_per_a": 5, "dc_resistance_ohm": 4,
            "diaphragm_area_m2": 0.005, "frequency_hz": [50, 100, 200],
            "box_volume_m3": 0.001, "voltage_rms_v": 1, "xmax_m": 0.01,
        }
        result = catalog.execute("lumped-speaker", params)
        return result["values"]["fs_hz"]

    def test_resonance_formula_holds_across_mass_and_compliance(self):
        for moving_mass_kg, compliance_m_per_n in [(0.005, 0.0005), (0.02, 0.0001), (0.008, 0.0003)]:
            with self.subTest(moving_mass_kg=moving_mass_kg, compliance_m_per_n=compliance_m_per_n):
                expected = 1 / (2 * math.pi * math.sqrt(moving_mass_kg * compliance_m_per_n))
                self.assertAlmostEqual(self._fs_hz(moving_mass_kg, compliance_m_per_n), expected, places=6)


class LatencyBudgetSerialSumTests(unittest.TestCase):
    """serial_latency_ms = sum(buffer_samples)/sample_rate_hz*1000 +
    sum(other_stage_ms); uncompensated_drift_ms_per_hour = ppm*3.6 (ppm
    of an hour, in milliseconds: 1e-6 * 3_600_000). Both re-derived here
    from first principles (unit conversion, not sourced from the
    implementation) and checked across several buffer/stage/ppm
    combinations, not just the one point the shared golden fixture
    already covers. Negative clock_difference_ppm is outside this
    method's declared applicability (rejected by the implementation), so
    only non-negative ppm values are exercised here."""

    def _values(self, sample_rate_hz, buffer_samples, other_stage_ms, clock_difference_ppm):
        params = {
            "sample_rate_hz": sample_rate_hz, "buffer_samples": buffer_samples,
            "other_stage_ms": other_stage_ms, "clock_difference_ppm": clock_difference_ppm,
        }
        return catalog.execute("latency-budget", params)["values"]

    def test_serial_sum_and_ppm_conversion_hold_across_inputs(self):
        cases = [
            (48000, [480, 960], [10, 20], 50),
            (44100, [256, 512, 128], [5], 100),
            (96000, [960], [0, 0, 15], 0),
        ]
        for sample_rate_hz, buffer_samples, other_stage_ms, clock_difference_ppm in cases:
            with self.subTest(sample_rate_hz=sample_rate_hz, buffer_samples=buffer_samples,
                               other_stage_ms=other_stage_ms, clock_difference_ppm=clock_difference_ppm):
                values = self._values(sample_rate_hz, buffer_samples, other_stage_ms, clock_difference_ppm)
                expected_serial = sum(buffer_samples) / sample_rate_hz * 1000 + sum(other_stage_ms)
                expected_drift = clock_difference_ppm * 3.6
                self.assertAlmostEqual(values["serial_latency_ms"], expected_serial, places=6)
                self.assertAlmostEqual(values["uncompensated_drift_ms_per_hour"], expected_drift, places=6)


class MicrophoneSensitivityDbConversionTests(unittest.TestCase):
    """All four outputs are plain dB/dBV conversions, re-derived here from
    first principles (20*log10 of a ratio), not sourced from the
    implementation: sensitivity_dbv_per_pa = 20*log10(Vpa), signal/noise
    SPL = 20*log10(level / Vpa / 20uPa reference), and
    snr_db = 20*log10(signal/noise). Checked across 3 different
    sensitivity/noise/signal combinations spanning the Microphone suite
    (the shared golden fixture only covers one point)."""

    def _values(self, sensitivity_mv_per_pa, noise_rms_v, signal_rms_v):
        params = {
            "sensitivity_mv_per_pa": sensitivity_mv_per_pa,
            "noise_rms_v": noise_rms_v, "signal_rms_v": signal_rms_v,
        }
        return catalog.execute("microphone-sensitivity", params)["values"]

    def test_db_conversions_hold_across_sensitivity_and_levels(self):
        cases = [(10, 1e-5, 0.01), (20, 5e-6, 0.02), (5, 2e-5, 0.005)]
        for sensitivity_mv_per_pa, noise_rms_v, signal_rms_v in cases:
            with self.subTest(sensitivity_mv_per_pa=sensitivity_mv_per_pa,
                               noise_rms_v=noise_rms_v, signal_rms_v=signal_rms_v):
                values = self._values(sensitivity_mv_per_pa, noise_rms_v, signal_rms_v)
                vpa = sensitivity_mv_per_pa / 1000
                self.assertAlmostEqual(values["sensitivity_dbv_per_pa"], 20 * math.log10(vpa), places=6)
                self.assertAlmostEqual(values["signal_spl_db"], 20 * math.log10(signal_rms_v / vpa / 20e-6), places=6)
                self.assertAlmostEqual(values["equivalent_noise_spl_db"], 20 * math.log10(noise_rms_v / vpa / 20e-6), places=6)
                self.assertAlmostEqual(values["snr_db"], 20 * math.log10(signal_rms_v / noise_rms_v), places=6)


class GccPhatTdoaKnownShiftTests(unittest.TestCase):
    """gcc-phat-tdoa's actual algorithm (FFT cross-correlation with phase-
    transform weighting) is not independently re-implemented here -- that
    would just duplicate the implementation and risk copying its own
    mistakes. Instead the ground truth is established by construction:
    an impulse in `reference` and the same impulse shifted by a known,
    chosen integer sample count in `delayed` has a mathematically
    unambiguous true delay, independent of how the algorithm finds it.
    The algorithm must recover exactly that constructed shift, and
    tdoa_s = delay_samples/sample_rate_hz and
    doa_deg = degrees(asin(tdoa_s*sound_speed_m_s/spacing_m)) are then
    checked against that same independently known shift -- not against
    the implementation's own tau. Checked across 3 different shift/
    sample-rate/spacing/sound-speed combinations, all within each case's
    physically valid lag window (spacing_m/sound_speed_m_s*sample_rate_hz)."""

    def _values(self, n, ref_index, shift, sample_rate_hz, spacing_m, sound_speed_m_s):
        reference = [0.0] * n
        reference[ref_index] = 1.0
        delayed = [0.0] * n
        delayed[ref_index + shift] = 1.0
        params = {
            "reference": reference, "delayed": delayed, "sample_rate_hz": sample_rate_hz,
            "spacing_m": spacing_m, "sound_speed_m_s": sound_speed_m_s,
        }
        return catalog.execute("gcc-phat-tdoa", params)["values"]

    def test_recovers_exact_constructed_shift_and_doa(self):
        cases = [
            (512, 200, 7, 48000, 0.1, 343),
            (512, 200, -4, 48000, 0.05, 343),
            (256, 100, 3, 16000, 0.08, 340),
        ]
        for n, ref_index, shift, sample_rate_hz, spacing_m, sound_speed_m_s in cases:
            with self.subTest(shift=shift, sample_rate_hz=sample_rate_hz, spacing_m=spacing_m, sound_speed_m_s=sound_speed_m_s):
                values = self._values(n, ref_index, shift, sample_rate_hz, spacing_m, sound_speed_m_s)
                expected_tau = shift / sample_rate_hz
                expected_doa = math.degrees(math.asin(max(-1.0, min(1.0, expected_tau * sound_speed_m_s / spacing_m))))
                self.assertEqual(values["delay_samples"], shift)
                self.assertAlmostEqual(values["tdoa_s"], expected_tau, places=10)
                self.assertAlmostEqual(values["doa_deg"], expected_doa, places=6)


if __name__ == "__main__":
    unittest.main()
