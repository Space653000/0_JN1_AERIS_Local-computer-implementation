"""Bounded sampled tonal-EQ decision without physical or listening claims."""
from __future__ import annotations

import math


ARRAYS = {"frequency_hz", "measured_level_db", "target_level_db", "spatial_spread_db"}
SCALARS = {
    "level_uncertainty_db": (0.0, 40.0), "maximum_boost_db": (0.0, 60.0),
    "maximum_cut_db": (0.0, 60.0), "available_headroom_db": (0.0, 60.0),
    "headroom_reserve_db": (0.0, 40.0), "smoothing_octaves": (0.0, 8.0),
    "maximum_smoothing_octaves": (0.0, 8.0), "unresolved_peak_db": (0.0, 120.0),
    "maximum_unresolved_peak_db": (0.0, 120.0), "room_notch_depth_db": (0.0, 120.0),
    "maximum_boostable_notch_depth_db": (0.0, 120.0), "loudness_match_error_db": (0.0, 40.0),
    "maximum_loudness_match_error_db": (0.0, 40.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared tonal value outside bounded applicability")


def validate(parameters):
    expected = ARRAYS | set(SCALARS) | {"model", "normalization_mode"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied sampled tonal-EQ contract required")
    if parameters["model"] != "SUPPLIED_SAMPLED_TONAL_EQ" or parameters["normalization_mode"] != "ABSOLUTE_LEVEL_MATCHED":
        raise ValueError("only absolute level-matched sampled tonal input is supported")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    arrays = [parameters[key] for key in ARRAYS]
    if any(not isinstance(values, list) for values in arrays) or not 3 <= len(parameters["frequency_hz"]) <= 2048:
        raise ValueError("bounded sampled tonal arrays required")
    count = len(parameters["frequency_hz"])
    if any(len(values) != count for values in arrays):
        raise ValueError("frequency, response, target and spatial arrays must align")
    for frequency in parameters["frequency_hz"]:
        _number(frequency, 1.0, 100000.0)
    if any(right <= left for left, right in zip(parameters["frequency_hz"], parameters["frequency_hz"][1:])):
        raise ValueError("strictly increasing unique frequency samples required")
    for key in ("measured_level_db", "target_level_db"):
        for level in parameters[key]:
            _number(level, -120.0, 200.0)
    for spread in parameters["spatial_spread_db"]:
        _number(spread, 0.0, 80.0)


def analyze(parameters):
    validate(parameters)
    p = parameters
    corrections = [target - measured for target, measured in zip(p["target_level_db"], p["measured_level_db"])]
    boost_upper = max(max(0.0, value) + spread + p["level_uncertainty_db"] for value, spread in zip(corrections, p["spatial_spread_db"]))
    cut_upper = max(max(0.0, -value) + spread + p["level_uncertainty_db"] for value, spread in zip(corrections, p["spatial_spread_db"]))
    required_headroom = boost_upper + p["headroom_reserve_db"]
    checks = [
        {"id": "SMOOTHING_RESOLUTION", "actual": p["smoothing_octaves"], "limit": p["maximum_smoothing_octaves"],
         "passed": p["smoothing_octaves"] <= p["maximum_smoothing_octaves"], "on_failure": "REDUCE_SMOOTHING_AND_RECHECK_NARROW_RESONANCES"},
        {"id": "UNRESOLVED_RESONANCE", "actual": p["unresolved_peak_db"], "limit": p["maximum_unresolved_peak_db"],
         "passed": p["unresolved_peak_db"] <= p["maximum_unresolved_peak_db"], "on_failure": "RESOLVE_NARROW_RESONANCE_BEFORE_TONAL_EQ"},
        {"id": "BOOST_BOUND", "actual": boost_upper, "limit": p["maximum_boost_db"],
         "passed": boost_upper <= p["maximum_boost_db"], "on_failure": "REDUCE_BOOST_OR_REVISE_TRANSDUCER_AND_ACOUSTIC_RESPONSE"},
        {"id": "CUT_BOUND", "actual": cut_upper, "limit": p["maximum_cut_db"],
         "passed": cut_upper <= p["maximum_cut_db"], "on_failure": "REVISE_TARGET_OR_FILTER_ALLOCATION"},
        {"id": "HEADROOM", "actual": required_headroom, "limit": p["available_headroom_db"],
         "passed": required_headroom <= p["available_headroom_db"], "on_failure": "RESERVE_SIGNAL_HEADROOM_BEFORE_APPLYING_EQ"},
        {"id": "ROOM_NOTCH_POLICY", "actual": p["room_notch_depth_db"], "limit": p["maximum_boostable_notch_depth_db"],
         "passed": p["room_notch_depth_db"] <= p["maximum_boostable_notch_depth_db"], "on_failure": "DO_NOT_BOOST_DEEP_ROOM_CANCELLATION"},
        {"id": "LOUDNESS_MATCH", "actual": p["loudness_match_error_db"], "limit": p["maximum_loudness_match_error_db"],
         "passed": p["loudness_match_error_db"] <= p["maximum_loudness_match_error_db"], "on_failure": "LEVEL_MATCH_BEFORE_PERCEPTUAL_COMPARISON"},
    ]
    return {
        "proposed_correction_db": corrections, "boost_upper_db": boost_upper, "cut_upper_db": cut_upper,
        "required_headroom_db": required_headroom, "checks": checks,
        "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "deep_notch_boost_authorized": False, "listening_preference_verified": False,
        "physical_measurement_verified": False,
        "counter_hypotheses": [
            "Room cancellation rather than driver deficit",
            "Measurement window or smoothing rather than tonal imbalance",
            "Level mismatch rather than listener preference",
        ],
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
