"""Independent R020 reconstruction of bounded R018 tonal assertions."""
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
    from .speaker_tonal import validate

    validate(parameters)
    if not isinstance(candidate, dict):
        raise ValueError("tonal candidate object required")
    p = parameters
    corrections = [p["target_level_db"][index] - p["measured_level_db"][index] for index in range(len(p["frequency_hz"]))]
    boost_candidates = [max(0.0, correction) + p["spatial_spread_db"][index] + p["level_uncertainty_db"] for index, correction in enumerate(corrections)]
    cut_candidates = [max(0.0, -correction) + p["spatial_spread_db"][index] + p["level_uncertainty_db"] for index, correction in enumerate(corrections)]
    boost_upper = max(boost_candidates)
    cut_upper = max(cut_candidates)
    headroom = boost_upper + p["headroom_reserve_db"]
    rows = [
        {"id": "SMOOTHING_RESOLUTION", "actual": p["smoothing_octaves"], "limit": p["maximum_smoothing_octaves"], "passed": p["smoothing_octaves"] <= p["maximum_smoothing_octaves"], "on_failure": "REDUCE_SMOOTHING_AND_RECHECK_NARROW_RESONANCES"},
        {"id": "UNRESOLVED_RESONANCE", "actual": p["unresolved_peak_db"], "limit": p["maximum_unresolved_peak_db"], "passed": p["unresolved_peak_db"] <= p["maximum_unresolved_peak_db"], "on_failure": "RESOLVE_NARROW_RESONANCE_BEFORE_TONAL_EQ"},
        {"id": "BOOST_BOUND", "actual": boost_upper, "limit": p["maximum_boost_db"], "passed": boost_upper <= p["maximum_boost_db"], "on_failure": "REDUCE_BOOST_OR_REVISE_TRANSDUCER_AND_ACOUSTIC_RESPONSE"},
        {"id": "CUT_BOUND", "actual": cut_upper, "limit": p["maximum_cut_db"], "passed": cut_upper <= p["maximum_cut_db"], "on_failure": "REVISE_TARGET_OR_FILTER_ALLOCATION"},
        {"id": "HEADROOM", "actual": headroom, "limit": p["available_headroom_db"], "passed": headroom <= p["available_headroom_db"], "on_failure": "RESERVE_SIGNAL_HEADROOM_BEFORE_APPLYING_EQ"},
        {"id": "ROOM_NOTCH_POLICY", "actual": p["room_notch_depth_db"], "limit": p["maximum_boostable_notch_depth_db"], "passed": p["room_notch_depth_db"] <= p["maximum_boostable_notch_depth_db"], "on_failure": "DO_NOT_BOOST_DEEP_ROOM_CANCELLATION"},
        {"id": "LOUDNESS_MATCH", "actual": p["loudness_match_error_db"], "limit": p["maximum_loudness_match_error_db"], "passed": p["loudness_match_error_db"] <= p["maximum_loudness_match_error_db"], "on_failure": "LEVEL_MATCH_BEFORE_PERCEPTUAL_COMPARISON"},
    ]
    expected = {
        "proposed_correction_db": corrections, "boost_upper_db": boost_upper, "cut_upper_db": cut_upper,
        "required_headroom_db": headroom, "checks": rows,
        "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "deep_notch_boost_authorized": False, "listening_preference_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Room cancellation rather than driver deficit", "Measurement window or smoothing rather than tonal imbalance", "Level mismatch rather than listener preference"],
        "next_discriminating_experiment": "REPEAT_SPATIALLY_AVERAGED_LEVEL_MATCHED_RESPONSE_WITH_FINE_SMOOTHING_AND_BYPASS_COMPARISON",
        "model_assumptions": [
            "Corrections are pointwise supplied-target differences, not designed filter coefficients",
            "Spatial spread and level uncertainty are conservatively added in dB for screening",
            "Headroom requirement includes the declared reserve",
            "No interpolation, audibility model or listener preference inference",
        ],
        "unresolved": [
            "Realizable filter response, phase, latency and clipping",
            "Room/fixture versus transducer causal attribution",
            "Listening validation, calibrated measurement and qualified Human acceptance",
        ],
    }
    if set(candidate) != set(expected):
        raise ValueError("exact tonal assertions required")
    differences = [{"field": key, "asserted": candidate[key], "expected": value} for key, value in expected.items() if not _same(candidate[key], value)]
    return {
        "domain": "speaker-tonal-context", "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT",
        "disagreements": differences,
        "observations": {"perceptual_scope": "level-matched numerical descriptors only", "unresolved": "Realizable filter and listener validation"},
        "human_approval": False, "role_l3_awarded": False,
        "scope": "bounded tonal correction, spatial spread and headroom report consistency only",
    }
