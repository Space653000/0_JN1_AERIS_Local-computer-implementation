"""Independent R071 reconstruction of bounded R026 room-correction assertions."""
from __future__ import annotations

import math


def _same(actual, expected):
    if isinstance(expected, dict): return isinstance(actual, dict) and set(actual) == set(expected) and all(_same(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list): return isinstance(actual, list) and len(actual) == len(expected) and all(_same(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, bool) or expected is None: return actual is expected
    if isinstance(expected, (int, float)): return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12)
    return actual == expected


def review(parameters, candidate):
    from .room_correction import validate, _values
    validate(parameters)
    if not isinstance(candidate, dict): raise ValueError("room-correction candidate object required")
    p = parameters; mean, spread, correction, boost_upper, cut_upper = _values(p)
    raw = [
        ("POSITION_COVERAGE", len(p["position_response_db"]), p["minimum_position_count"], ">=", "ADD_SPATIALLY_DISTRIBUTED_POSITIONS"),
        ("SPATIAL_SPREAD", max(spread), p["maximum_spatial_spread_db"], "<=", "WITHHOLD_GLOBAL_EQ_AND_RESOLVE_POSITION_DEPENDENCE"),
        ("BOOST_BOUND", boost_upper, p["maximum_boost_db"], "<=", "REDUCE_BOOST_OR_REVISE_ACOUSTIC_PLACEMENT"),
        ("CUT_BOUND", cut_upper, p["maximum_cut_db"], "<=", "REVISE_TARGET_OR_FILTER_ALLOCATION"),
        ("DEEP_NOTCH_POLICY", p["deep_notch_depth_db"], p["maximum_boostable_notch_depth_db"], "<=", "DO_NOT_INVERT_DEEP_POSITION_DEPENDENT_NULL"),
        ("FILTER_LATENCY", p["required_filter_latency_ms"], p["maximum_filter_latency_ms"], "<=", "REDUCE_FILTER_ORDER_OR_REVISE_LATENCY_BUDGET"),
        ("NONMINIMUM_PHASE_BANDS", p["nonminimum_phase_band_count"], p["maximum_nonminimum_phase_band_count"], "<=", "WITHHOLD_MAGNITUDE_INVERSION_FOR_NONMINIMUM_PHASE_BANDS"),
    ]
    rows = [{"id": i, "actual": a, "limit": l, "operator": o, "passed": a <= l if o == "<=" else a >= l, "on_failure": f} for i, a, l, o, f in raw]
    expected = {
        "mean_response_db": mean, "spatial_spread_db": spread, "maximum_spatial_spread_db": max(spread), "proposed_correction_db": correction,
        "boost_upper_db": boost_upper, "cut_upper_db": cut_upper, "checks": rows,
        "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "realized_filter_verified": False, "minimum_phase_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Position-dependent cancellation rather than loudspeaker deficit", "Late reflection rather than minimum-phase peak", "Measurement alignment rather than stable room response"],
        "next_discriminating_experiment": "MEASURE_DENSE_MULTI_POSITION_COMPLEX_RESPONSE_AND_BYPASS_REALIZED_FILTER_WITH_LATENCY_HEADROOM_LOGGING",
        "model_assumptions": ["Arithmetic mean of supplied dB samples is a screening statistic", "No interpolation or complex transfer-function inversion", "Spatial spread and response uncertainty are deterministic bounds"],
        "unresolved": ["Complex phase and mixed-phase causality", "Realized filter response, stability, latency and headroom", "Calibrated multi-position measurement and qualified Human acceptance"],
    }
    if set(candidate) != set(expected): raise ValueError("exact room-correction assertions required")
    differences = [{"field": key, "asserted": candidate[key], "expected": value} for key, value in expected.items() if not _same(candidate[key], value)]
    return {"domain": "room-correction-spatial", "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT", "disagreements": differences,
            "observations": {"spatial_scope": "supplied positions only", "unresolved": "complex response and realized filter"},
            "human_approval": False, "role_l3_awarded": False, "scope": "bounded multi-position room-correction report consistency only"}
