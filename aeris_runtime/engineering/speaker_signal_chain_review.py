"""Independent R013 reconstruction of bounded R012 signal-chain assertions."""
from __future__ import annotations

import math


def _same(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual) == set(expected) and all(_same(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(_same(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, bool) or expected is None:
        return actual is expected
    if isinstance(expected, (int, float)):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12)
    return actual == expected


def review(parameters, candidate):
    from .speaker_signal_chain import validate

    validate(parameters)
    if not isinstance(candidate, dict):
        raise ValueError("speaker signal-chain candidate object required")
    p = parameters
    gains = p["stage_voltage_gains"]
    downstream = [math.prod(gains[index:]) for index in range(len(gains))]
    total_gain = downstream[0]
    contributions = [p["source_noise_rms_v"] * total_gain]
    contributions += [noise * downstream[index] for index, noise in enumerate(p["stage_input_noise_rms_v"])]
    nominal_noise = math.sqrt(math.fsum(value * value for value in contributions))
    noise_upper = nominal_noise * (1.0 + p["noise_relative_bound"])
    signal_rms = p["source_signal_rms_v"] * total_gain
    peak_v = signal_rms * p["crest_factor"]
    peak_a = peak_v / p["load_impedance_min_ohm"]
    loading_ratio = p["chain_input_impedance_ohm"] / p["source_impedance_ohm"]
    raw = [
        ("OUTPUT_NOISE_BUDGET", noise_upper, p["maximum_output_noise_rms_v"], "<=", "REDUCE_REFERRED_NOISE_OR_GAIN_BANDWIDTH"),
        ("VOLTAGE_HEADROOM", peak_v, p["available_output_peak_v"], "<=", "REDUCE_GAIN_OR_INCREASE_AVAILABLE_RAIL_HEADROOM"),
        ("CURRENT_HEADROOM", peak_a, p["available_output_peak_a"], "<=", "REDUCE_PEAK_DRIVE_OR_INCREASE_CURRENT_CAPABILITY"),
        ("LOAD_STABILITY", p["load_impedance_min_ohm"], p["minimum_supported_load_ohm"], ">=", "REVISE_LOAD_OR_VALIDATE_AMPLIFIER_STABILITY"),
        ("SOURCE_LOADING", loading_ratio, p["minimum_loading_ratio"], ">=", "INCREASE_INPUT_IMPEDANCE_OR_BUFFER_SOURCE"),
        ("PHASE_MARGIN", p["phase_margin_deg"], p["minimum_phase_margin_deg"], ">=", "REVISE_LOOP_COMPENSATION_AND_LOAD_NETWORK"),
    ]
    rows = [{"id": identifier, "actual": actual, "limit": limit, "operator": operator,
             "passed": actual <= limit if operator == "<=" else actual >= limit, "on_failure": action}
            for identifier, actual, limit, operator, action in raw]
    expected = {
        "total_voltage_gain": total_gain, "output_noise_contributions_rms_v": contributions,
        "nominal_output_noise_rms_v": nominal_noise, "output_noise_upper_rms_v": noise_upper,
        "nominal_output_signal_rms_v": signal_rms, "required_output_peak_v": peak_v,
        "required_output_peak_a": peak_a, "loading_ratio": loading_ratio, "checks": rows,
        "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "stability_measurement_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Ground-loop pickup rather than intrinsic stage noise", "Reactive load or cable network rather than nominal resistance", "Supply droop rather than small-signal gain error"],
        "next_discriminating_experiment": "MEASURE_STAGE_REFERRED_NOISE_AND_COMPLEX_LOAD_RAIL_CURRENT_AT_DECLARED_CREST_FACTOR",
        "model_assumptions": ["Stage input-noise contributions are mutually uncorrelated and bandwidth-integrated", "All voltage gains are positive scalar RMS gains", "Peak load current uses the declared minimum resistive magnitude only", "Declared phase margin is supplied metadata, not measured by this adapter"],
        "unresolved": ["Noise correlation, spectral density and ground/coupling paths", "Complex load, cable, rail droop and transient protection behavior", "Bench stability, calibrated measurement and qualified Human acceptance"],
    }
    if set(candidate) != set(expected):
        raise ValueError("exact speaker signal-chain assertions required")
    differences = [{"field": key, "asserted": candidate[key], "expected": value} for key, value in expected.items() if not _same(candidate[key], value)]
    return {
        "domain": "speaker-signal-chain-headroom", "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT",
        "disagreements": differences,
        "observations": {"stability_scope": "declared phase/load screening only", "unresolved": "complex load and bench stability"},
        "human_approval": False, "role_l3_awarded": False,
        "scope": "bounded gain, referred-noise, loading and peak headroom report consistency only",
    }
