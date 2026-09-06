"""Bounded R026 multi-position room-correction feasibility screen."""
from __future__ import annotations

import math


SCALARS = {
    "response_uncertainty_db": (0.0, 40.0), "minimum_position_count": (2, 1000),
    "maximum_spatial_spread_db": (0.0, 120.0), "maximum_boost_db": (0.0, 120.0),
    "maximum_cut_db": (0.0, 120.0), "deep_notch_depth_db": (0.0, 200.0),
    "maximum_boostable_notch_depth_db": (0.0, 200.0), "required_filter_latency_ms": (0.0, 1e6),
    "maximum_filter_latency_ms": (0.0, 1e6), "nonminimum_phase_band_count": (0, 100000),
    "maximum_nonminimum_phase_band_count": (0, 100000),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared room-correction value outside bounded applicability")


def validate(parameters):
    expected = set(SCALARS) | {"model", "frequency_hz", "position_response_db", "target_response_db"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied multi-position room-correction contract required")
    if parameters["model"] != "SUPPLIED_MULTI_POSITION_ROOM_CORRECTION":
        raise ValueError("unsupported room-correction model")
    for key, bounds in SCALARS.items(): _number(parameters[key], *bounds)
    frequencies = parameters["frequency_hz"]
    target = parameters["target_response_db"]
    positions = parameters["position_response_db"]
    if not isinstance(frequencies, list) or not isinstance(target, list) or not 3 <= len(frequencies) <= 2048 or len(target) != len(frequencies):
        raise ValueError("aligned bounded frequency and target arrays required")
    if any(right <= left for left, right in zip(frequencies, frequencies[1:])):
        raise ValueError("strictly increasing unique frequencies required")
    for value in frequencies: _number(value, 1.0, 100000.0)
    for value in target: _number(value, -200.0, 200.0)
    if not isinstance(positions, list) or not 2 <= len(positions) <= 1000:
        raise ValueError("bounded position response matrix required")
    for row in positions:
        if not isinstance(row, list) or len(row) != len(frequencies): raise ValueError("rectangular position response matrix required")
        for value in row: _number(value, -200.0, 200.0)


def _values(parameters):
    positions = parameters["position_response_db"]
    count = len(positions)
    mean = [math.fsum(row[index] for row in positions) / count for index in range(len(parameters["frequency_hz"]))]
    spread = [max(row[index] for row in positions) - min(row[index] for row in positions) for index in range(len(mean))]
    correction = [target - value for target, value in zip(parameters["target_response_db"], mean)]
    boost_upper = max(max(0.0, value) + parameters["response_uncertainty_db"] for value in correction)
    cut_upper = max(max(0.0, -value) + parameters["response_uncertainty_db"] for value in correction)
    return mean, spread, correction, boost_upper, cut_upper


def analyze(parameters):
    validate(parameters); p = parameters
    mean, spread, correction, boost_upper, cut_upper = _values(p)
    rows = [
        ("POSITION_COVERAGE", len(p["position_response_db"]), p["minimum_position_count"], ">=", "ADD_SPATIALLY_DISTRIBUTED_POSITIONS"),
        ("SPATIAL_SPREAD", max(spread), p["maximum_spatial_spread_db"], "<=", "WITHHOLD_GLOBAL_EQ_AND_RESOLVE_POSITION_DEPENDENCE"),
        ("BOOST_BOUND", boost_upper, p["maximum_boost_db"], "<=", "REDUCE_BOOST_OR_REVISE_ACOUSTIC_PLACEMENT"),
        ("CUT_BOUND", cut_upper, p["maximum_cut_db"], "<=", "REVISE_TARGET_OR_FILTER_ALLOCATION"),
        ("DEEP_NOTCH_POLICY", p["deep_notch_depth_db"], p["maximum_boostable_notch_depth_db"], "<=", "DO_NOT_INVERT_DEEP_POSITION_DEPENDENT_NULL"),
        ("FILTER_LATENCY", p["required_filter_latency_ms"], p["maximum_filter_latency_ms"], "<=", "REDUCE_FILTER_ORDER_OR_REVISE_LATENCY_BUDGET"),
        ("NONMINIMUM_PHASE_BANDS", p["nonminimum_phase_band_count"], p["maximum_nonminimum_phase_band_count"], "<=", "WITHHOLD_MAGNITUDE_INVERSION_FOR_NONMINIMUM_PHASE_BANDS"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o, "passed": a <= l if o == "<=" else a >= l, "on_failure": f} for i, a, l, o, f in rows]
    return {
        "mean_response_db": mean, "spatial_spread_db": spread, "maximum_spatial_spread_db": max(spread),
        "proposed_correction_db": correction, "boost_upper_db": boost_upper, "cut_upper_db": cut_upper,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "realized_filter_verified": False, "minimum_phase_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Position-dependent cancellation rather than loudspeaker deficit", "Late reflection rather than minimum-phase peak", "Measurement alignment rather than stable room response"],
        "next_discriminating_experiment": "MEASURE_DENSE_MULTI_POSITION_COMPLEX_RESPONSE_AND_BYPASS_REALIZED_FILTER_WITH_LATENCY_HEADROOM_LOGGING",
        "model_assumptions": ["Arithmetic mean of supplied dB samples is a screening statistic", "No interpolation or complex transfer-function inversion", "Spatial spread and response uncertainty are deterministic bounds"],
        "unresolved": ["Complex phase and mixed-phase causality", "Realized filter response, stability, latency and headroom", "Calibrated multi-position measurement and qualified Human acceptance"],
    }
