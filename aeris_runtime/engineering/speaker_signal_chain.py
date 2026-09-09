"""Bounded R012 speaker signal-chain noise, loading and headroom budget."""
from __future__ import annotations

import math


ARRAYS = {"stage_voltage_gains", "stage_input_noise_rms_v"}
SCALARS = {
    "source_noise_rms_v": (0.0, 100.0), "source_signal_rms_v": (0.0, 1000.0),
    "source_impedance_ohm": (1e-9, 1e12), "chain_input_impedance_ohm": (1e-9, 1e15),
    "minimum_loading_ratio": (1.0, 1e9), "crest_factor": (1.0, 1000.0),
    "load_impedance_min_ohm": (1e-9, 1e9), "minimum_supported_load_ohm": (1e-9, 1e9),
    "available_output_peak_v": (0.0, 1e9), "available_output_peak_a": (0.0, 1e9),
    "maximum_output_noise_rms_v": (0.0, 1e6), "noise_relative_bound": (0.0, 10.0),
    "phase_margin_deg": (0.0, 180.0), "minimum_phase_margin_deg": (0.0, 180.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared signal-chain value outside bounded applicability")


def validate(parameters):
    expected = ARRAYS | set(SCALARS) | {"model"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied speaker signal-chain contract required")
    if parameters["model"] != "SUPPLIED_SPEAKER_SIGNAL_CHAIN":
        raise ValueError("unsupported signal-chain model")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    gains = parameters["stage_voltage_gains"]
    noises = parameters["stage_input_noise_rms_v"]
    if not isinstance(gains, list) or not isinstance(noises, list) or not 1 <= len(gains) <= 64 or len(gains) != len(noises):
        raise ValueError("aligned bounded gain and input-noise stages required")
    for gain in gains:
        _number(gain, 1e-12, 1e9)
    for noise in noises:
        _number(noise, 0.0, 100.0)


def _budget(parameters):
    gains = parameters["stage_voltage_gains"]
    downstream = []
    for index in range(len(gains)):
        downstream.append(math.prod(gains[index:]))
    total_gain = downstream[0]
    contributions = [parameters["source_noise_rms_v"] * total_gain]
    contributions.extend(noise * downstream[index] for index, noise in enumerate(parameters["stage_input_noise_rms_v"]))
    nominal_noise = math.sqrt(math.fsum(value * value for value in contributions))
    return total_gain, contributions, nominal_noise


def analyze(parameters):
    validate(parameters)
    p = parameters
    total_gain, contributions, nominal_noise = _budget(p)
    noise_upper = nominal_noise * (1.0 + p["noise_relative_bound"])
    signal_rms = p["source_signal_rms_v"] * total_gain
    peak_v = signal_rms * p["crest_factor"]
    peak_a = peak_v / p["load_impedance_min_ohm"]
    loading_ratio = p["chain_input_impedance_ohm"] / p["source_impedance_ohm"]
    rows = [
        ("OUTPUT_NOISE_BUDGET", noise_upper, p["maximum_output_noise_rms_v"], "<=", "REDUCE_REFERRED_NOISE_OR_GAIN_BANDWIDTH"),
        ("VOLTAGE_HEADROOM", peak_v, p["available_output_peak_v"], "<=", "REDUCE_GAIN_OR_INCREASE_AVAILABLE_RAIL_HEADROOM"),
        ("CURRENT_HEADROOM", peak_a, p["available_output_peak_a"], "<=", "REDUCE_PEAK_DRIVE_OR_INCREASE_CURRENT_CAPABILITY"),
        ("LOAD_STABILITY", p["load_impedance_min_ohm"], p["minimum_supported_load_ohm"], ">=", "REVISE_LOAD_OR_VALIDATE_AMPLIFIER_STABILITY"),
        ("SOURCE_LOADING", loading_ratio, p["minimum_loading_ratio"], ">=", "INCREASE_INPUT_IMPEDANCE_OR_BUFFER_SOURCE"),
        ("PHASE_MARGIN", p["phase_margin_deg"], p["minimum_phase_margin_deg"], ">=", "REVISE_LOOP_COMPENSATION_AND_LOAD_NETWORK"),
    ]
    checks = [{"id": identifier, "actual": actual, "limit": limit, "operator": operator,
               "passed": actual <= limit if operator == "<=" else actual >= limit, "on_failure": action}
              for identifier, actual, limit, operator, action in rows]
    return {
        "total_voltage_gain": total_gain,
        "output_noise_contributions_rms_v": contributions,
        "nominal_output_noise_rms_v": nominal_noise,
        "output_noise_upper_rms_v": noise_upper,
        "nominal_output_signal_rms_v": signal_rms,
        "required_output_peak_v": peak_v,
        "required_output_peak_a": peak_a,
        "loading_ratio": loading_ratio,
        "checks": checks,
        "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "stability_measurement_verified": False,
        "physical_measurement_verified": False,
        "counter_hypotheses": [
            "Ground-loop pickup rather than intrinsic stage noise",
            "Reactive load or cable network rather than nominal resistance",
            "Supply droop rather than small-signal gain error",
        ],
        "next_discriminating_experiment": "MEASURE_STAGE_REFERRED_NOISE_AND_COMPLEX_LOAD_RAIL_CURRENT_AT_DECLARED_CREST_FACTOR",
        "model_assumptions": [
            "Stage input-noise contributions are mutually uncorrelated and bandwidth-integrated",
            "All voltage gains are positive scalar RMS gains",
            "Peak load current uses the declared minimum resistive magnitude only",
            "Declared phase margin is supplied metadata, not measured by this adapter",
        ],
        "unresolved": [
            "Noise correlation, spectral density and ground/coupling paths",
            "Complex load, cable, rail droop and transient protection behavior",
            "Bench stability, calibrated measurement and qualified Human acceptance",
        ],
    }
