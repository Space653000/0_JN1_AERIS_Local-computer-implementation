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


if __name__ == "__main__":
    unittest.main()
