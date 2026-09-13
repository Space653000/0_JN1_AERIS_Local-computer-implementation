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


class ReliabilityBinomialZeroFailuresTests(unittest.TestCase):
    """reliability-binomial's implementation calls
    scipy.stats.beta.ppf(confidence, failures+1, trials-failures) (the
    general Clopper-Pearson exact one-sided upper bound) -- re-calling
    the same library function with the same arguments would just check
    that the parameter mapping was retyped correctly, not that the
    underlying statistics are right. For the zero-failures case
    specifically there is a genuinely independent closed form: observing
    zero failures in n trials, the one-sided upper confidence bound p
    solves (1-p)^n = alpha (the probability of seeing zero failures if
    the true failure rate were exactly p), so p = 1 - alpha**(1/n) --
    derived here from that probability argument, not from calling
    scipy.stats.beta at all. Checked across 3 different trial-count/
    confidence combinations, all with zero observed failures."""

    def _upper(self, trials, failures, confidence):
        params = {"trials": trials, "failures": failures, "confidence": confidence}
        return catalog.execute("reliability-binomial", params)["values"]["one_sided_upper_failure_probability"]

    def test_zero_failures_closed_form_holds_across_trials_and_confidence(self):
        cases = [(100, 0.95), (50, 0.90), (200, 0.99)]
        for trials, confidence in cases:
            with self.subTest(trials=trials, confidence=confidence):
                alpha = 1 - confidence
                expected = 1 - alpha ** (1 / trials)
                self.assertAlmostEqual(self._upper(trials, 0, confidence), expected, places=10)


class LinearArrayPatternSteeringPeakTests(unittest.TestCase):
    """Two independent invariants, re-derived from the array-pattern
    definition itself rather than the implementation: (1) at the exact
    steering angle, every element's phase term is identically zero by
    definition (direction == steering direction), so the coherently
    summed normalized power there must equal exactly 1 regardless of
    array geometry, frequency, or steering angle -- this isn't a
    property the implementation computes so much as a mathematical
    identity of what "steering" means. (2) alias_free_spacing is the
    textbook spatial-Nyquist grating-lobe criterion, max element
    spacing <= half a wavelength (c/(2*freq)), re-derived here and
    checked against both a compliant and a non-compliant geometry.
    Checked across 5 different array/frequency/steering combinations."""

    def _values(self, positions_m, frequency_hz, sound_speed_m_s, steering_deg):
        params = {
            "positions_m": positions_m, "frequency_hz": frequency_hz,
            "sound_speed_m_s": sound_speed_m_s, "steering_deg": steering_deg,
        }
        return catalog.execute("linear-array-pattern", params)["values"]

    def test_peak_at_steering_angle_and_alias_free_criterion(self):
        cases = [
            ([0, 0.02, 0.04, 0.06], 1000, 343, 0),
            ([0, 0.05, 0.10], 2000, 343, 0),
            ([0, 0.03, 0.09, 0.15], 1500, 340, 30),
            ([0, 0.1], 500, 343, -15),
            ([0, 0.2, 0.4], 3000, 343, 0),
        ]
        for positions_m, frequency_hz, sound_speed_m_s, steering_deg in cases:
            with self.subTest(positions_m=positions_m, frequency_hz=frequency_hz,
                               sound_speed_m_s=sound_speed_m_s, steering_deg=steering_deg):
                values = self._values(positions_m, frequency_hz, sound_speed_m_s, steering_deg)
                angles = values["angles_deg"]
                closest_index = min(range(len(angles)), key=lambda i: abs(angles[i] - steering_deg))
                self.assertAlmostEqual(values["normalized_power"][closest_index], 1.0, places=8)
                max_spacing = max(b - a for a, b in zip(positions_m, positions_m[1:]))
                expected_alias_free = max_spacing <= sound_speed_m_s / (2 * frequency_hz)
                self.assertEqual(values["alias_free_spacing"], expected_alias_free)


if __name__ == "__main__":
    unittest.main()
