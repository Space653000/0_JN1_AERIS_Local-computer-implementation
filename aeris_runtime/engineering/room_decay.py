"""Bounded R023 multi-position room-decay fit screening."""
from __future__ import annotations

import math


ARRAYS = {"position_ids", "decay_rate_db_per_s", "fit_span_db", "noise_margin_db", "fit_r_squared"}
SCALARS = {
    "frequency_band_hz": (1.0, 100000.0), "minimum_fit_span_db": (0.0, 120.0),
    "minimum_noise_margin_db": (0.0, 120.0), "minimum_fit_r_squared": (0.0, 1.0),
    "minimum_valid_position_fraction": (0.0, 1.0), "maximum_valid_rt60_s": (0.0, 1000.0),
    "maximum_valid_rt60_spread_s": (0.0, 1000.0), "window_duration_s": (0.0, 10000.0),
    "minimum_window_duration_s": (0.0, 10000.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared room-decay value outside bounded applicability")


def validate(parameters):
    expected = ARRAYS | set(SCALARS) | {"model"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied room-decay position-fit contract required")
    if parameters["model"] != "SUPPLIED_ROOM_DECAY_POSITION_FITS":
        raise ValueError("unsupported room-decay model")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    positions = parameters["position_ids"]
    if not isinstance(positions, list) or not 2 <= len(positions) <= 256 or any(not isinstance(item, str) or not item.strip() for item in positions) or len(set(positions)) != len(positions):
        raise ValueError("bounded unique room position IDs required")
    count = len(positions)
    for key in ARRAYS - {"position_ids"}:
        values = parameters[key]
        if not isinstance(values, list) or len(values) != count:
            raise ValueError("aligned position-fit arrays required")
    for rate in parameters["decay_rate_db_per_s"]:
        _number(rate, 1e-12, 1e9)
    for key in ("fit_span_db", "noise_margin_db"):
        for value in parameters[key]:
            _number(value, 0.0, 200.0)
    for value in parameters["fit_r_squared"]:
        _number(value, 0.0, 1.0)


def analyze(parameters):
    validate(parameters)
    p = parameters
    rt60 = [60.0 / rate for rate in p["decay_rate_db_per_s"]]
    valid = [index for index in range(len(rt60)) if p["fit_span_db"][index] >= p["minimum_fit_span_db"] and p["noise_margin_db"][index] >= p["minimum_noise_margin_db"] and p["fit_r_squared"][index] >= p["minimum_fit_r_squared"]]
    fraction = len(valid) / len(rt60)
    valid_rt60 = [rt60[index] for index in valid]
    maximum = max(valid_rt60) if valid_rt60 else None
    spread = max(valid_rt60) - min(valid_rt60) if valid_rt60 else None
    checks = [
        {"id": "VALID_POSITION_COVERAGE", "actual": fraction, "limit": p["minimum_valid_position_fraction"], "operator": ">=", "passed": fraction >= p["minimum_valid_position_fraction"], "on_failure": "ADD_POSITIONS_WITH_VALID_DECAY_FITS"},
        {"id": "VALID_RT60_MAXIMUM", "actual": maximum, "limit": p["maximum_valid_rt60_s"], "operator": "<=", "passed": maximum is not None and maximum <= p["maximum_valid_rt60_s"], "on_failure": "REVISE_ABSORPTION_PLACEMENT_OR_DECLARED_DECAY_TARGET"},
        {"id": "SPATIAL_DECAY_SPREAD", "actual": spread, "limit": p["maximum_valid_rt60_spread_s"], "operator": "<=", "passed": spread is not None and spread <= p["maximum_valid_rt60_spread_s"], "on_failure": "MAP_POSITION_DEPENDENCE_BEFORE_GLOBAL_ROOM_CLAIM"},
        {"id": "WINDOW_DURATION", "actual": p["window_duration_s"], "limit": p["minimum_window_duration_s"], "operator": ">=", "passed": p["window_duration_s"] >= p["minimum_window_duration_s"], "on_failure": "EXTEND_IR_WINDOW_BEFORE_DECAY_EXTRAPOLATION"},
    ]
    return {
        "rt60_s": rt60, "valid_position_ids": [p["position_ids"][index] for index in valid],
        "valid_position_fraction": fraction, "maximum_valid_rt60_s": maximum,
        "valid_rt60_spread_s": spread, "checks": checks,
        "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "diffuse_field_verified": False, "full_room_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Noise floor rather than long decay", "Local modal ringing rather than broadband reverberation", "Window truncation rather than absorption change"],
        "next_discriminating_experiment": "REPEAT_CALIBRATED_IR_DECAY_AT_ADDITIONAL_POSITIONS_WITH_EXPLICIT_FIT_INTERVAL_AND_NOISE_FLOOR",
        "model_assumptions": ["Each supplied positive slope is a linear decay-rate magnitude", "RT60 is 60/rate extrapolation only", "Valid-position screening does not prove a diffuse field"],
        "unresolved": ["Frequency-band and position representativeness", "Late nonlinearity, modal structure and diffuse-field validity", "Calibrated IR acquisition and qualified Human acceptance"],
    }
