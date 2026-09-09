"""Independent R072 reconstruction of bounded R023 room-decay assertions."""
from __future__ import annotations

import math


def _same(actual, expected):
    if isinstance(expected, dict): return isinstance(actual, dict) and set(actual) == set(expected) and all(_same(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list): return isinstance(actual, list) and len(actual) == len(expected) and all(_same(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, bool) or expected is None: return actual is expected
    if isinstance(expected, (int, float)): return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12)
    return actual == expected


def review(parameters, candidate):
    from .room_decay import validate
    validate(parameters)
    if not isinstance(candidate, dict): raise ValueError("room-decay candidate object required")
    p = parameters
    rt60 = [60.0 / rate for rate in p["decay_rate_db_per_s"]]
    valid = [index for index in range(len(rt60)) if p["fit_span_db"][index] >= p["minimum_fit_span_db"] and p["noise_margin_db"][index] >= p["minimum_noise_margin_db"] and p["fit_r_squared"][index] >= p["minimum_fit_r_squared"]]
    fraction = len(valid) / len(rt60); values = [rt60[index] for index in valid]
    maximum = max(values) if values else None; spread = max(values) - min(values) if values else None
    rows = [
        {"id": "VALID_POSITION_COVERAGE", "actual": fraction, "limit": p["minimum_valid_position_fraction"], "operator": ">=", "passed": fraction >= p["minimum_valid_position_fraction"], "on_failure": "ADD_POSITIONS_WITH_VALID_DECAY_FITS"},
        {"id": "VALID_RT60_MAXIMUM", "actual": maximum, "limit": p["maximum_valid_rt60_s"], "operator": "<=", "passed": maximum is not None and maximum <= p["maximum_valid_rt60_s"], "on_failure": "REVISE_ABSORPTION_PLACEMENT_OR_DECLARED_DECAY_TARGET"},
        {"id": "SPATIAL_DECAY_SPREAD", "actual": spread, "limit": p["maximum_valid_rt60_spread_s"], "operator": "<=", "passed": spread is not None and spread <= p["maximum_valid_rt60_spread_s"], "on_failure": "MAP_POSITION_DEPENDENCE_BEFORE_GLOBAL_ROOM_CLAIM"},
        {"id": "WINDOW_DURATION", "actual": p["window_duration_s"], "limit": p["minimum_window_duration_s"], "operator": ">=", "passed": p["window_duration_s"] >= p["minimum_window_duration_s"], "on_failure": "EXTEND_IR_WINDOW_BEFORE_DECAY_EXTRAPOLATION"},
    ]
    expected = {
        "rt60_s": rt60, "valid_position_ids": [p["position_ids"][index] for index in valid],
        "valid_position_fraction": fraction, "maximum_valid_rt60_s": maximum, "valid_rt60_spread_s": spread,
        "checks": rows, "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "diffuse_field_verified": False, "full_room_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Noise floor rather than long decay", "Local modal ringing rather than broadband reverberation", "Window truncation rather than absorption change"],
        "next_discriminating_experiment": "REPEAT_CALIBRATED_IR_DECAY_AT_ADDITIONAL_POSITIONS_WITH_EXPLICIT_FIT_INTERVAL_AND_NOISE_FLOOR",
        "model_assumptions": ["Each supplied positive slope is a linear decay-rate magnitude", "RT60 is 60/rate extrapolation only", "Valid-position screening does not prove a diffuse field"],
        "unresolved": ["Frequency-band and position representativeness", "Late nonlinearity, modal structure and diffuse-field validity", "Calibrated IR acquisition and qualified Human acceptance"],
    }
    if set(candidate) != set(expected): raise ValueError("exact room-decay assertions required")
    differences = [{"field": key, "asserted": candidate[key], "expected": value} for key, value in expected.items() if not _same(candidate[key], value)]
    return {"domain": "room-decay-spatial", "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT", "disagreements": differences,
            "observations": {"field_scope": "valid sampled positions only", "unresolved": "modal and diffuse-field validity"},
            "human_approval": False, "role_l3_awarded": False, "scope": "bounded multi-position decay-fit report consistency only"}
