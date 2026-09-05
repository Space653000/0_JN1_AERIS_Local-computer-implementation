"""Independent R025 reconstruction of bounded R019 bass-limiter assertions."""
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
    from .speaker_bass_limiter import validate

    validate(parameters)
    if not isinstance(candidate, dict):
        raise ValueError("bass-limiter candidate object required")
    p = parameters
    boosted = [excursion * math.exp(math.log(10.0) * boost / 20.0) for excursion, boost in zip(p["baseline_peak_excursion_mm"], p["requested_boost_db"])]
    worst_excursion = max(boosted) * (1.0 + p["excursion_relative_bound"])
    temperature_upper = p["predicted_coil_temperature_c"] + p["temperature_bound_c"]
    raw = [
        ("EXCURSION_ENVELOPE", worst_excursion, p["maximum_peak_excursion_mm"], "<=", "REDUCE_BASS_BOOST_OR_DRIVE_BEFORE_XMAX"),
        ("THERMAL_ENVELOPE", temperature_upper, p["maximum_coil_temperature_c"], "<=", "REDUCE_DUTY_OR_DRIVE_AND_REVALIDATE_THERMAL_STATE"),
        ("AMPLIFIER_VOLTAGE_HEADROOM", p["required_amplifier_peak_v"], p["available_amplifier_peak_v"], "<=", "REDUCE_BOOST_OR_INCREASE_RAIL_HEADROOM"),
        ("ATTACK_TIME", p["attack_ms"], p["maximum_attack_ms"], "<=", "SHORTEN_ATTACK_TO_INTERCEPT_DECLARED_PEAK"),
        ("RELEASE_MINIMUM", p["release_ms"], p["minimum_release_ms"], ">=", "LENGTHEN_RELEASE_TO_REDUCE_ENVELOPE_PUMPING"),
        ("RELEASE_MAXIMUM", p["release_ms"], p["maximum_release_ms"], "<=", "SHORTEN_RELEASE_TO_RESTORE_GAIN_WITHIN_DECLARED_USE_CASE"),
        ("CONTENT_CREST_COVERAGE", p["content_crest_factor"], p["minimum_crest_factor"], ">=", "EXPAND_CONTENT_CREST_FACTOR_ENVELOPE"),
    ]
    rows = [{"id": identifier, "actual": actual, "limit": limit, "operator": operator,
             "passed": actual <= limit if operator == "<=" else actual >= limit, "on_failure": action}
            for identifier, actual, limit, operator, action in raw]
    expected = {
        "boosted_peak_excursion_mm": boosted, "worst_excursion_upper_mm": worst_excursion,
        "coil_temperature_upper_c": temperature_upper, "checks": rows,
        "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "limiter_audio_quality_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Amplifier rail clipping rather than excursion limiting", "Thermal drift rather than static EQ mismatch", "Fixture leakage rather than insufficient low-frequency motor output"],
        "next_discriminating_experiment": "REPLAY_DECLARED_CREST_FACTOR_SWEEP_WITH_EXCURSION_COIL_TEMPERATURE_RAIL_AND_GAIN_REDUCTION_LOGGING",
        "model_assumptions": ["Excursion scales with requested linear voltage gain at each supplied frequency", "Relative excursion and absolute temperature bounds are deterministic screening limits", "Attack/release checks do not simulate program-dependent detector dynamics"],
        "unresolved": ["Program-dependent limiter pumping and distortion", "Frequency-dependent impedance, rail droop and dynamic thermal feedback", "Calibrated excursion/temperature measurement, durability and qualified Human acceptance"],
    }
    if set(candidate) != set(expected):
        raise ValueError("exact bass-limiter assertions required")
    differences = [{"field": key, "asserted": candidate[key], "expected": value} for key, value in expected.items() if not _same(candidate[key], value)]
    return {
        "domain": "speaker-bass-protection", "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT",
        "disagreements": differences,
        "observations": {"protection_scope": "declared envelope only", "unresolved": "dynamic observer and physical protection behavior"},
        "human_approval": False, "role_l3_awarded": False,
        "scope": "bounded bass boost, excursion, thermal and limiter-envelope report consistency only",
    }
