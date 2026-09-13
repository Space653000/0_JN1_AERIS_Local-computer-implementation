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


class SpectralAnalysisCoherentSineTests(unittest.TestCase):
    """Two textbook Fourier-analysis identities, re-derived from first
    principles rather than the implementation: for a pure sinusoid
    A*sin(2*pi*k*n/N) sampled coherently (integer periods across the
    window, rectangular window, no leakage), the single-sided FFT
    magnitude at bin k equals exactly the peak amplitude A, and the
    time-domain RMS equals A/sqrt(2) regardless of coherent sampling
    (RMS is a plain time-domain property of any sinusoid). Checked
    across 3 different sample-count/bin/amplitude/sample-rate
    combinations, each constructed here (not sourced from the shared
    golden fixture) so the true amplitude is known independently of
    whatever the implementation computes."""

    def _values(self, n, bin_k, amplitude, sample_rate_hz):
        samples = [amplitude * math.sin(2 * math.pi * bin_k * t / n) for t in range(n)]
        params = {"samples": samples, "sample_rate_hz": sample_rate_hz, "window": "rectangular"}
        return catalog.execute("spectral-analysis", params)["values"]

    def test_coherent_bin_amplitude_and_rms_hold_across_signals(self):
        cases = [(1024, 64, 1.0, 8192), (512, 32, 2.5, 4000), (2048, 100, 0.7, 16000)]
        for n, bin_k, amplitude, sample_rate_hz in cases:
            with self.subTest(n=n, bin_k=bin_k, amplitude=amplitude, sample_rate_hz=sample_rate_hz):
                values = self._values(n, bin_k, amplitude, sample_rate_hz)
                self.assertAlmostEqual(values["amplitude"][bin_k], amplitude, places=8)
                self.assertAlmostEqual(values["rms"], amplitude / math.sqrt(2), places=8)


class RequirementTraceabilityCoverageRatioTests(unittest.TestCase):
    """coverage = (count of requirements with at least one link) /
    (total requirement count) -- a plain ratio, re-derived here from the
    requirement/link definitions directly rather than the
    implementation. Checked across partial, full, and zero coverage
    (the zero case exercises an empty links list, a genuine edge case
    the single existing golden fixture doesn't reach)."""

    def _coverage(self, requirement_ids, test_ids, links):
        params = {"requirement_ids": requirement_ids, "test_ids": test_ids, "links": links}
        return catalog.execute("requirement-traceability", params)["values"]["coverage"]

    def test_coverage_ratio_holds_across_partial_full_and_zero_cases(self):
        cases = [
            (["R1", "R2"], ["T1"], [{"requirement_id": "R1", "test_id": "T1", "evidence_ref": "E1"}]),
            (["R1", "R2", "R3", "R4"], ["T1", "T2"],
             [{"requirement_id": "R1", "test_id": "T1", "evidence_ref": "E1"},
              {"requirement_id": "R2", "test_id": "T2", "evidence_ref": "E2"},
              {"requirement_id": "R3", "test_id": "T1", "evidence_ref": "E3"}]),
            (["R1"], ["T1"], []),
        ]
        for requirement_ids, test_ids, links in cases:
            with self.subTest(requirement_ids=requirement_ids, links=links):
                covered = {link["requirement_id"] for link in links}
                expected_coverage = len(covered) / len(requirement_ids)
                self.assertAlmostEqual(self._coverage(requirement_ids, test_ids, links), expected_coverage, places=10)


class HelmholtzPortResonanceTests(unittest.TestCase):
    """Ideal Helmholtz resonator frequency, re-derived from the textbook
    formula f = c/(2*pi) * sqrt(A/(L*V)) rather than the implementation.
    Checked across 3 different area/length/volume/sound-speed
    combinations, not just the one point the shared golden fixture
    already covers."""

    def _hz(self, area_m2, effective_length_m, volume_m3, sound_speed_m_s):
        params = {
            "area_m2": area_m2, "effective_length_m": effective_length_m,
            "volume_m3": volume_m3, "sound_speed_m_s": sound_speed_m_s,
        }
        return catalog.execute("helmholtz-port", params)["values"]["helmholtz_hz"]

    def test_resonance_formula_holds_across_geometry_and_sound_speed(self):
        cases = [(0.001, 0.1, 0.01, 343), (0.0005, 0.05, 0.002, 343), (0.002, 0.15, 0.03, 340)]
        for area_m2, effective_length_m, volume_m3, sound_speed_m_s in cases:
            with self.subTest(area_m2=area_m2, effective_length_m=effective_length_m,
                               volume_m3=volume_m3, sound_speed_m_s=sound_speed_m_s):
                expected = sound_speed_m_s / (2 * math.pi) * math.sqrt(area_m2 / (effective_length_m * volume_m3))
                self.assertAlmostEqual(self._hz(area_m2, effective_length_m, volume_m3, sound_speed_m_s), expected, places=6)


class ThermalRcResponseTests(unittest.TestCase):
    """First-order RC thermal circuit, re-derived from the textbook
    formulas rather than the implementation: steady_temperature_c =
    ambient + power*resistance (Ohm's-law analog), and
    temperature_c(t) = ambient + power*resistance*(1 - exp(-t/(R*C)))
    (the standard RC step response). Checked across 3 different power/
    resistance/capacity/ambient/time-series combinations, not just the
    one-time-constant point the shared golden fixture covers."""

    def _values(self, power_w, thermal_resistance_k_w, thermal_capacity_j_k, ambient_c, limit_c, time_s):
        params = {
            "power_w": power_w, "thermal_resistance_k_w": thermal_resistance_k_w,
            "thermal_capacity_j_k": thermal_capacity_j_k, "ambient_c": ambient_c,
            "limit_c": limit_c, "time_s": time_s,
        }
        return catalog.execute("thermal-rc", params)["values"]

    def test_steady_state_and_step_response_hold_across_parameters(self):
        cases = [
            (2, 10, 5, 20, 60, [0, 50, 100]),
            (3, 8, 4, 25, 80, [0, 16, 32, 64]),
            (1.5, 12, 6, 22, 55, [0, 72, 144]),
        ]
        for power_w, resistance, capacity, ambient_c, limit_c, time_s in cases:
            with self.subTest(power_w=power_w, resistance=resistance, capacity=capacity, ambient_c=ambient_c):
                values = self._values(power_w, resistance, capacity, ambient_c, limit_c, time_s)
                expected_steady = ambient_c + power_w * resistance
                tau = resistance * capacity
                expected_temps = [ambient_c + power_w * resistance * (1 - math.exp(-t / tau)) for t in time_s]
                self.assertAlmostEqual(values["steady_temperature_c"], expected_steady, places=8)
                for actual, expected in zip(values["temperature_c"], expected_temps):
                    self.assertAlmostEqual(actual, expected, places=8)


class ResponsePhaseGroupDelayTests(unittest.TestCase):
    """Group delay = -d(phase)/d(omega). For a perfectly linear phase
    response phase(f) = -2*pi*f*delay (constructed here with a known,
    chosen delay, not sourced from the implementation), the true group
    delay is that same constant at every frequency point, including the
    array edges -- a mathematical identity of what "constant group
    delay" means, independent of how the implementation's numerical
    derivative (np.gradient) computes it. Checked across 3 different
    delay values and frequency grids, including one with uneven
    spacing."""

    def _group_delay(self, frequency_hz, delay_s):
        phase_rad = [-2 * math.pi * f * delay_s for f in frequency_hz]
        params = {"frequency_hz": frequency_hz, "magnitude_db": [0] * len(frequency_hz),
                   "phase_rad": phase_rad, "smoothing_octaves": 0}
        return catalog.execute("response-phase-delay", params)["values"]["group_delay_s"]

    def test_constant_group_delay_holds_at_every_point(self):
        cases = [
            ([100, 200, 300], 0.001),
            ([50, 150, 250, 350], 0.0005),
            ([1000, 2000, 3000], 0.0002),
        ]
        for frequency_hz, delay_s in cases:
            with self.subTest(frequency_hz=frequency_hz, delay_s=delay_s):
                for actual in self._group_delay(frequency_hz, delay_s):
                    self.assertAlmostEqual(actual, delay_s, places=8)


class FractionalOctaveParsevalTests(unittest.TestCase):
    """Parseval's theorem: a pure sinusoid of amplitude A has mean-square
    power A^2/2, independent of how the implementation bins that energy
    into 1/N-octave bands. When the tone's frequency lands on an exact
    FFT bin (no spectral leakage -- chosen here via integer
    cycles-per-record, not sourced from the implementation), *all* of
    that A^2/2 must land in the single third-octave band whose analytic
    edges (center*2^(+-1/(2*fraction)), independently recomputed here)
    contain the tone, and the sum across every returned band must equal
    A^2/2. Checked across 3 different frequencies, sample rates, band
    fractions and amplitudes."""

    def _band_containing(self, frequency_hz, fraction):
        for k in range(-12 * fraction, 6 * fraction + 1):
            center = 1000 * 2 ** (k / fraction)
            lo, hi = center / 2 ** (1 / (2 * fraction)), center * 2 ** (1 / (2 * fraction))
            if lo <= frequency_hz < hi:
                return center
        raise AssertionError("no analytic band covers this frequency")

    def _band_powers(self, frequency_hz, sample_rate_hz, n, fraction, amplitude):
        samples = [amplitude * math.sin(2 * math.pi * frequency_hz * i / sample_rate_hz) for i in range(n)]
        params = {"samples": samples, "sample_rate_hz": sample_rate_hz, "fraction": fraction}
        values = catalog.execute("fractional-octave", params)["values"]
        return dict(zip(values["centers_hz"], values["band_power_unit2"]))

    def test_tone_energy_lands_entirely_in_its_analytic_band(self):
        cases = [
            (512, 8192, 1024, 3, 1.0),
            (1000, 16000, 1600, 1, 2.0),
            (250, 8000, 800, 6, 0.5),
        ]
        for frequency_hz, sample_rate_hz, n, fraction, amplitude in cases:
            with self.subTest(frequency_hz=frequency_hz, sample_rate_hz=sample_rate_hz, fraction=fraction):
                powers = self._band_powers(frequency_hz, sample_rate_hz, n, fraction, amplitude)
                expected_power = amplitude ** 2 / 2
                target_center = self._band_containing(frequency_hz, fraction)
                self.assertAlmostEqual(powers[target_center], expected_power, places=8)
                self.assertAlmostEqual(sum(powers.values()), expected_power, places=8)


class UncertaintyPropagationGumLawTests(unittest.TestCase):
    """GUM's law of propagation of uncertainty is a bilinear form,
    combined = sqrt((s*u) @ correlation @ (s*u)), independently
    re-derived here at its two textbook extremes rather than copied from
    the implementation: with the default identity correlation (no
    covariance term is supplied), it collapses to plain root-sum-square
    of the individual contributions s_i*u_i; with every pair fully
    correlated (correlation matrix of all ones), it collapses to the
    absolute value of their plain sum, since sqrt((sum x)^2) = |sum x|.
    Checked across single- and multi-contributor cases, including a
    negative sensitivity coefficient."""

    def _combined(self, sensitivities, uncertainties, correlation_matrix, coverage_factor):
        params = {"sensitivity_coefficients": sensitivities, "standard_uncertainties": uncertainties,
                   "coverage_factor": coverage_factor}
        if correlation_matrix is not None:
            params["correlation_matrix"] = correlation_matrix
        values = catalog.execute("uncertainty-propagation", params)["values"]
        return values["combined_standard_uncertainty"], values["expanded_uncertainty"]

    def test_independent_contributors_combine_as_root_sum_square(self):
        cases = [([1.0, 2.0, 0.5], [0.1, 0.05, 0.2], 2.0), ([3.0], [0.02], 1.0)]
        for sensitivities, uncertainties, coverage_factor in cases:
            with self.subTest(sensitivities=sensitivities):
                contributions = [s * u for s, u in zip(sensitivities, uncertainties)]
                expected_combined = math.sqrt(sum(c * c for c in contributions))
                combined, expanded = self._combined(sensitivities, uncertainties, None, coverage_factor)
                self.assertAlmostEqual(combined, expected_combined, places=8)
                self.assertAlmostEqual(expanded, coverage_factor * expected_combined, places=8)

    def test_fully_correlated_contributors_combine_as_plain_sum(self):
        cases = [([1.0, 2.0, 0.5], [0.1, 0.05, 0.2], 2.0), ([1.5, -2.0], [0.3, 0.1], 3.0)]
        for sensitivities, uncertainties, coverage_factor in cases:
            with self.subTest(sensitivities=sensitivities):
                n = len(sensitivities)
                all_ones = [[1.0] * n for _ in range(n)]
                contributions = [s * u for s, u in zip(sensitivities, uncertainties)]
                expected_combined = abs(sum(contributions))
                combined, expanded = self._combined(sensitivities, uncertainties, all_ones, coverage_factor)
                self.assertAlmostEqual(combined, expected_combined, places=8)
                self.assertAlmostEqual(expanded, coverage_factor * expected_combined, places=8)


class LevelStatisticsEnergyAverageTests(unittest.TestCase):
    """Leq is the standard acoustics equivalent-continuous-level formula,
    10*log10(time-weighted average of 10^(L/10)) -- independently
    recomputed here directly from that textbook definition (the
    implementation instead subtracts the maximum level first purely for
    numerical stability, an equivalent but differently-shaped
    computation). L10/L50/L90 are checked against the plain definition
    of a duration-weighted exceedance percentile ("the level exceeded
    X% of the time"), worked out by hand for stratified duration splits
    where the answer is unambiguous."""

    def _values(self, levels_db, durations_s):
        return catalog.execute("level-statistics", {"levels_db": levels_db, "durations_s": durations_s})["values"]

    def test_leq_matches_energy_average_definition_across_distributions(self):
        cases = [([60, 80], [1, 1]), ([50, 60, 70], [1, 1, 1]), ([40, 90], [9, 1])]
        for levels_db, durations_s in cases:
            with self.subTest(levels_db=levels_db, durations_s=durations_s):
                total = sum(durations_s)
                expected_leq = 10 * math.log10(
                    sum(d * 10 ** (l / 10) for l, d in zip(levels_db, durations_s)) / total)
                values = self._values(levels_db, durations_s)
                self.assertAlmostEqual(values["leq_db"], expected_leq, places=8)
                self.assertAlmostEqual(values["duration_s"], total, places=8)

    def test_percentile_exceedance_matches_duration_weighted_definition(self):
        # Three equal-duration thirds: the quietest third is exceeded 90%
        # of the time (L90), the middle third 50% of the time (L50), and
        # only the loudest third is exceeded just 10% of the time (L10).
        values = self._values([50, 60, 70], [1, 1, 1])
        self.assertAlmostEqual(values["l10_db"], 70, places=8)
        self.assertAlmostEqual(values["l50_db"], 60, places=8)
        self.assertAlmostEqual(values["l90_db"], 50, places=8)
        # A quiet level dominating 90% of the duration is exceeded at
        # every one of the standard percentile thresholds (10/50/90 all
        # fall inside that 90% majority window).
        dominant = self._values([40, 90], [9, 1])
        for key in ("l10_db", "l50_db", "l90_db"):
            self.assertAlmostEqual(dominant[key], 40, places=8)


class LeakageToleranceHagenPoiseuilleTests(unittest.TestCase):
    """Hagen-Poiseuille laminar pipe flow resistance, R = 8*mu*L/(pi*r^4),
    is a standard physics formula, independently recomputed here rather
    than copied from the implementation. Since R is proportional to
    r^-4, elementary calculus gives dR/dr = -4R/r, so linearized
    first-order uncertainty propagation must satisfy
    u_R = |dR/dr|*u_r = 4*R*u_r/r -- derived from the power rule, not
    from the implementation's own expression for it. Checked across 3
    different geometries and viscosities."""

    def _values(self, radius_m, length_m, viscosity_pa_s, radius_uncertainty_m):
        params = {"radius_m": radius_m, "length_m": length_m, "viscosity_pa_s": viscosity_pa_s,
                   "radius_standard_uncertainty_m": radius_uncertainty_m}
        return catalog.execute("leakage-tolerance", params)["values"]

    def test_resistance_and_linearized_uncertainty_hold_across_geometries(self):
        cases = [(0.001, 0.01, 1.8e-05, 1e-05), (0.002, 0.02, 2.0e-05, 2e-05), (0.0005, 0.005, 1.5e-05, 1e-06)]
        for radius_m, length_m, viscosity_pa_s, radius_uncertainty_m in cases:
            with self.subTest(radius_m=radius_m, length_m=length_m):
                expected_r = 8 * viscosity_pa_s * length_m / (math.pi * radius_m ** 4)
                expected_u = 4 * expected_r * radius_uncertainty_m / radius_m
                values = self._values(radius_m, length_m, viscosity_pa_s, radius_uncertainty_m)
                self.assertAlmostEqual(values["flow_resistance_pa_s_m3"], expected_r, places=2)
                self.assertAlmostEqual(values["standard_uncertainty_pa_s_m3"], expected_u, places=2)


class CorrelationOutliersPerfectLineTests(unittest.TestCase):
    """For data constructed to lie exactly on a line y = a*x + b (a
    mathematical fact about ordinary least squares, not sourced from
    the implementation), the fitted slope and intercept must recover
    a and b exactly, the Pearson correlation must be exactly +-1
    (perfect fit means zero residual variance), and the slope's
    standard error must be exactly zero (no scatter around the fit).
    Checked for both a positive and a negative slope. Outlier flagging
    is checked with an extreme, unambiguous outlier and with a dataset
    that has none -- values chosen far past any reasonable modified
    Z-score threshold in either direction, rather than probing the
    implementation's exact 3.5 cutoff."""

    def _values(self, x, y):
        return catalog.execute("correlation-outliers", {"x": x, "y": y})["values"]

    def test_perfect_line_recovers_exact_slope_intercept_and_correlation(self):
        cases = [([1, 2, 3, 4], [3, 5, 7, 9], 2, 1), ([0, 1, 2, 3, 4], [10, 8, 6, 4, 2], -2, 10)]
        for x, y, expected_slope, expected_intercept in cases:
            with self.subTest(x=x, y=y):
                values = self._values(x, y)
                self.assertAlmostEqual(values["slope"], expected_slope, places=8)
                self.assertAlmostEqual(values["intercept"], expected_intercept, places=8)
                self.assertAlmostEqual(abs(values["pearson_r"]), 1.0, places=8)
                self.assertAlmostEqual(values["slope_standard_error"], 0.0, places=8)

    def test_extreme_outlier_is_flagged_and_tight_cluster_is_not(self):
        with_outlier = self._values([1, 2, 3, 4, 5], [10, 11, 9, 10, 1000])
        self.assertEqual(with_outlier["outlier_indices"], [4])
        without_outlier = self._values([1, 2, 3, 4, 5], [10, 11, 9, 10, 10.5])
        self.assertEqual(without_outlier["outlier_indices"], [])


class ResonanceCharacterizationHalfPowerTests(unittest.TestCase):
    """Half-power (-3 dB) bandwidth is the frequency span where amplitude
    falls to peak/sqrt(2) -- constructed here so the crossing amplitude
    lands exactly on a grid point on each side (no interpolation
    ambiguity), so the resulting bandwidth and Q = f_peak / bandwidth
    are known exactly by hand rather than sourced from the
    implementation. Checked for two different peak positions,
    bandwidths and amplitude scales."""

    def _values(self, frequency_hz, amplitude):
        return catalog.execute("resonance-characterization",
                                {"frequency_hz": frequency_hz, "amplitude": amplitude})["values"]

    def test_half_power_bandwidth_and_q_hold_at_exact_grid_crossings(self):
        s2 = math.sqrt(2)
        cases = [
            ([80, 90, 100, 110, 120], [0.5, s2, 2, s2, 0.5], 100, 20, 5.0),
            ([10, 20, 30, 40, 50, 60], [0.1, 2 * s2, 4, 2 * s2, 0.1, 0.05], 30, 20, 1.5),
        ]
        for frequency_hz, amplitude, expected_peak, expected_bandwidth, expected_q in cases:
            with self.subTest(frequency_hz=frequency_hz):
                values = self._values(frequency_hz, amplitude)
                self.assertAlmostEqual(values["peak_frequency_hz"], expected_peak, places=8)
                self.assertAlmostEqual(values["half_power_bandwidth_hz"], expected_bandwidth, places=8)
                self.assertAlmostEqual(values["q_estimate"], expected_q, places=8)


class TransferCoherenceNoiselessGainTests(unittest.TestCase):
    """For a noiseless LTI system where the response is exactly a
    constant real gain applied to the reference (response = gain *
    reference, no delay, no added noise) -- a case constructed here,
    not sourced from the implementation -- the transfer function must
    equal that same real gain at every valid frequency bin (zero
    imaginary part), and coherence must be exactly 1 everywhere: the
    response is perfectly predictable from the reference, which is the
    textbook definition of unit coherence. Checked for a positive and a
    negative gain."""

    def _values(self, gain, fs=8192, n=1024):
        reference = [math.sin(2 * math.pi * 200 * i / fs) + 0.5 * math.sin(2 * math.pi * 500 * i / fs) +
                     0.3 * math.sin(2 * math.pi * 1000 * i / fs) for i in range(n)]
        response = [gain * v for v in reference]
        return catalog.execute("transfer-coherence",
                                {"reference": reference, "response": response, "sample_rate_hz": fs})["values"]

    def test_constant_gain_and_unit_coherence_hold_at_every_bin(self):
        for gain in (3.0, -2.0):
            with self.subTest(gain=gain):
                values = self._values(gain)
                self.assertGreater(len(values["coherence"]), 0)
                for real, imag, coherence in zip(values["transfer_real"], values["transfer_imag"], values["coherence"]):
                    self.assertAlmostEqual(real, gain, places=6)
                    self.assertAlmostEqual(imag, 0.0, places=6)
                    self.assertAlmostEqual(coherence, 1.0, places=6)


class CircuitNoiseBudgetStandardFormulaTests(unittest.TestCase):
    """Four independent, textbook physics/electronics formulas, each
    re-derived here from first principles rather than copied from the
    implementation: Johnson-Nyquist thermal noise
    sqrt(4*k*T*R*bandwidth); ideal ADC quantization noise
    fullscale/(2^bits*sqrt(12)); root-sum-square combination of
    uncorrelated noise sources (thermal, amplifier density integrated
    over bandwidth, quantization); and the jitter-limited SNR ceiling
    -20*log10(2*pi*f*jitter). Checked across 2 different circuit
    configurations."""

    def _values(self, resistance_ohm, temperature_k, bandwidth_hz, amplifier_noise_v_per_sqrt_hz,
                adc_fullscale_v, adc_bits, signal_frequency_hz, jitter_rms_s):
        params = {"resistance_ohm": resistance_ohm, "temperature_k": temperature_k, "bandwidth_hz": bandwidth_hz,
                   "amplifier_noise_v_per_sqrt_hz": amplifier_noise_v_per_sqrt_hz, "adc_fullscale_v": adc_fullscale_v,
                   "adc_bits": adc_bits, "signal_frequency_hz": signal_frequency_hz, "jitter_rms_s": jitter_rms_s}
        return catalog.execute("circuit-noise-budget", params)["values"]

    def test_noise_formulas_hold_across_circuit_configurations(self):
        boltzmann = 1.380649e-23
        cases = [
            (1000, 300, 20000, 1e-9, 2, 16, 1000, 1e-9),
            (4700, 290, 8000, 2e-9, 3.3, 12, 5000, 5e-10),
        ]
        for resistance_ohm, temperature_k, bandwidth_hz, density, fullscale_v, bits, freq_hz, jitter_s in cases:
            with self.subTest(resistance_ohm=resistance_ohm, adc_bits=bits):
                thermal = math.sqrt(4 * boltzmann * temperature_k * resistance_ohm * bandwidth_hz)
                quantization = fullscale_v / (2 ** bits * math.sqrt(12))
                rss = math.sqrt(thermal ** 2 + density ** 2 * bandwidth_hz + quantization ** 2)
                jitter_limit_db = -20 * math.log10(2 * math.pi * freq_hz * jitter_s)
                values = self._values(resistance_ohm, temperature_k, bandwidth_hz, density, fullscale_v, bits,
                                       freq_hz, jitter_s)
                self.assertAlmostEqual(values["johnson_noise_rms_v"], thermal, places=12)
                self.assertAlmostEqual(values["quantization_rms_v"], quantization, places=12)
                self.assertAlmostEqual(values["input_noise_rss_v"], rss, places=12)
                self.assertAlmostEqual(values["jitter_snr_limit_db"], jitter_limit_db, places=8)


class MonteCarloLinearCombinationTests(unittest.TestCase):
    """For Y = sum(c_i * X_i) with independent X_i ~ N(mean_i, std_i),
    elementary probability theory (linearity of expectation, variance
    of a sum of independent variables) gives E[Y] = sum(c_i*mean_i) and
    SD[Y] = sqrt(sum((c_i*std_i)^2)) -- independently recomputed here
    from the raw inputs, not read off the implementation's own
    analytic_mean/analytic_sd output fields. The large-trial-count
    Monte Carlo simulation must also converge close to that same
    independently-derived value, which confirms the simulation and the
    closed form agree rather than both being wrong the same way.
    Checked across two different linear combinations."""

    def _values(self, means, standard_deviations, coefficients, trials, seed):
        params = {"means": means, "standard_deviations": standard_deviations, "coefficients": coefficients,
                   "trials": trials, "seed": seed}
        return catalog.execute("monte-carlo", params)["values"]

    def test_analytic_and_simulated_moments_match_independent_formula(self):
        cases = [([10, 20], [1, 2], [2, -1], 20000, 42), ([5, 0, 3], [0.5, 1, 0.2], [1, 3, -2], 50000, 7)]
        for means, stds, coefficients, trials, seed in cases:
            with self.subTest(means=means, coefficients=coefficients):
                expected_mean = sum(m * c for m, c in zip(means, coefficients))
                expected_sd = math.sqrt(sum((s * c) ** 2 for s, c in zip(stds, coefficients)))
                values = self._values(means, stds, coefficients, trials, seed)
                self.assertAlmostEqual(values["analytic_mean"], expected_mean, places=8)
                self.assertAlmostEqual(values["analytic_sd"], expected_sd, places=8)
                mean_tolerance = 0.05 * max(1, abs(expected_mean)) + 0.1
                sd_tolerance = 0.1 * expected_sd + 0.05
                self.assertLess(abs(values["mean"] - expected_mean), mean_tolerance)
                self.assertLess(abs(values["standard_deviation"] - expected_sd), sd_tolerance)


if __name__ == "__main__":
    unittest.main()
