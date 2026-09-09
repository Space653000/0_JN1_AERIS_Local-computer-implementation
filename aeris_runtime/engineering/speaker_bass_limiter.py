"""Bounded R019 bass boost, excursion, thermal and limiter envelope."""
from __future__ import annotations

import math


ARRAYS = {"frequency_hz", "requested_boost_db", "baseline_peak_excursion_mm"}
SCALARS = {
    "maximum_peak_excursion_mm": (1e-12, 1e6), "excursion_relative_bound": (0.0, 10.0),
    "predicted_coil_temperature_c": (-273.15, 5000.0), "maximum_coil_temperature_c": (-273.15, 5000.0),
    "temperature_bound_c": (0.0, 1000.0), "required_amplifier_peak_v": (0.0, 1e9),
    "available_amplifier_peak_v": (0.0, 1e9), "attack_ms": (0.0, 1e6),
    "maximum_attack_ms": (0.0, 1e6), "release_ms": (0.0, 1e7),
    "minimum_release_ms": (0.0, 1e7), "maximum_release_ms": (0.0, 1e7),
    "content_crest_factor": (1.0, 1000.0), "minimum_crest_factor": (1.0, 1000.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared bass-limiter value outside bounded applicability")


def validate(parameters):
    expected = ARRAYS | set(SCALARS) | {"model"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied bass-limiter contract required")
    if parameters["model"] != "SUPPLIED_BASS_LIMITER_ENVELOPE":
        raise ValueError("unsupported bass-limiter model")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    arrays = [parameters[key] for key in ARRAYS]
    if any(not isinstance(values, list) for values in arrays) or not 3 <= len(parameters["frequency_hz"]) <= 2048:
        raise ValueError("bounded aligned bass-envelope arrays required")
    if any(len(values) != len(parameters["frequency_hz"]) for values in arrays):
        raise ValueError("frequency, boost and excursion arrays must align")
    for frequency in parameters["frequency_hz"]:
        _number(frequency, 1.0, 100000.0)
    if any(right <= left for left, right in zip(parameters["frequency_hz"], parameters["frequency_hz"][1:])):
        raise ValueError("strictly increasing unique frequency samples required")
    for boost in parameters["requested_boost_db"]:
        _number(boost, -60.0, 60.0)
    for excursion in parameters["baseline_peak_excursion_mm"]:
        _number(excursion, 0.0, 1e6)
    if parameters["minimum_release_ms"] > parameters["maximum_release_ms"]:
        raise ValueError("invalid limiter release window")


def analyze(parameters):
    validate(parameters)
    p = parameters
    boosted = [excursion * 10.0 ** (boost / 20.0) for excursion, boost in zip(p["baseline_peak_excursion_mm"], p["requested_boost_db"])]
    worst_excursion = max(boosted) * (1.0 + p["excursion_relative_bound"])
    temperature_upper = p["predicted_coil_temperature_c"] + p["temperature_bound_c"]
    rows = [
        ("EXCURSION_ENVELOPE", worst_excursion, p["maximum_peak_excursion_mm"], "<=", "REDUCE_BASS_BOOST_OR_DRIVE_BEFORE_XMAX"),
        ("THERMAL_ENVELOPE", temperature_upper, p["maximum_coil_temperature_c"], "<=", "REDUCE_DUTY_OR_DRIVE_AND_REVALIDATE_THERMAL_STATE"),
        ("AMPLIFIER_VOLTAGE_HEADROOM", p["required_amplifier_peak_v"], p["available_amplifier_peak_v"], "<=", "REDUCE_BOOST_OR_INCREASE_RAIL_HEADROOM"),
        ("ATTACK_TIME", p["attack_ms"], p["maximum_attack_ms"], "<=", "SHORTEN_ATTACK_TO_INTERCEPT_DECLARED_PEAK"),
        ("RELEASE_MINIMUM", p["release_ms"], p["minimum_release_ms"], ">=", "LENGTHEN_RELEASE_TO_REDUCE_ENVELOPE_PUMPING"),
        ("RELEASE_MAXIMUM", p["release_ms"], p["maximum_release_ms"], "<=", "SHORTEN_RELEASE_TO_RESTORE_GAIN_WITHIN_DECLARED_USE_CASE"),
        ("CONTENT_CREST_COVERAGE", p["content_crest_factor"], p["minimum_crest_factor"], ">=", "EXPAND_CONTENT_CREST_FACTOR_ENVELOPE"),
    ]
    checks = [{"id": identifier, "actual": actual, "limit": limit, "operator": operator,
               "passed": actual <= limit if operator == "<=" else actual >= limit, "on_failure": action}
              for identifier, actual, limit, operator, action in rows]
    return {
        "boosted_peak_excursion_mm": boosted,
        "worst_excursion_upper_mm": worst_excursion,
        "coil_temperature_upper_c": temperature_upper,
        "checks": checks,
        "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "limiter_audio_quality_verified": False,
        "physical_measurement_verified": False,
        "counter_hypotheses": [
            "Amplifier rail clipping rather than excursion limiting",
            "Thermal drift rather than static EQ mismatch",
            "Fixture leakage rather than insufficient low-frequency motor output",
        ],
        "next_discriminating_experiment": "REPLAY_DECLARED_CREST_FACTOR_SWEEP_WITH_EXCURSION_COIL_TEMPERATURE_RAIL_AND_GAIN_REDUCTION_LOGGING",
        "model_assumptions": [
            "Excursion scales with requested linear voltage gain at each supplied frequency",
            "Relative excursion and absolute temperature bounds are deterministic screening limits",
            "Attack/release checks do not simulate program-dependent detector dynamics",
        ],
        "unresolved": [
            "Program-dependent limiter pumping and distortion",
            "Frequency-dependent impedance, rail droop and dynamic thermal feedback",
            "Calibrated excursion/temperature measurement, durability and qualified Human acceptance",
        ],
    }
