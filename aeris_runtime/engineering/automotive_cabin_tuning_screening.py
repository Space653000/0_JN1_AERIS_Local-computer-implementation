"""Bounded R063 automotive cabin tuning screening: does a declared
driver/rear-seat level spread stay within a declared bound, and was the
tuning validated under road-noise conditions rather than only in a parked
cabin, from supplied scalars only.

This directly guards against this role's two named failure modes: a
driver-seat-optimized tuning that harms rear-passenger level balance, and
a tuning validated only in a quiet parked cabin that road noise would
invalidate.
"""
from __future__ import annotations

import math

SCALARS = {"max_acceptable_seat_level_spread_db": (0.0, 200.0)}


def _number(value, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("finite declared automotive cabin tuning value outside bounded applicability")
    if low is not None and not low <= value <= high:
        raise ValueError("finite declared automotive cabin tuning value outside bounded applicability")


def validate(parameters):
    expected = {"model", "driver_seat_level_db", "rear_seat_level_db", "tuning_validated_under_road_noise"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied automotive cabin tuning screening contract required")
    if parameters["model"] != "SUPPLIED_AUTOMOTIVE_CABIN_TUNING_SCREEN":
        raise ValueError("unsupported automotive cabin tuning screening model")
    for key in ("driver_seat_level_db", "rear_seat_level_db"):
        if isinstance(parameters[key], bool) or not isinstance(parameters[key], (int, float)) or not math.isfinite(parameters[key]):
            raise ValueError("finite declared automotive cabin tuning value outside bounded applicability")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    if not isinstance(parameters["tuning_validated_under_road_noise"], bool):
        raise ValueError("boolean road-noise validation flag required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    driver, rear = p["driver_seat_level_db"], p["rear_seat_level_db"]
    spread = abs(driver - rear)
    validated_road = p["tuning_validated_under_road_noise"]
    raw = [
        ("SEAT_LEVEL_SPREAD_WITHIN_BOUND", spread <= p["max_acceptable_seat_level_spread_db"],
         "REBALANCE_THE_TUNING_ACROSS_SEATS_OR_RELAX_THE_LEVEL_SPREAD_TARGET"),
        ("TUNING_VALIDATED_UNDER_ROAD_NOISE", validated_road,
         "REVALIDATE_THE_TUNING_UNDER_REPRESENTATIVE_ROAD_NOISE_NOT_ONLY_A_PARKED_CABIN"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "driver_seat_level_db": driver, "rear_seat_level_db": rear, "seat_level_spread_db": spread,
        "tuning_validated_under_road_noise": validated_road,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Seat geometry/acoustic path difference rather than a true array/tuning defect",
                                "Vehicle speed change rather than a genuine noise-reduction regression"],
        "next_discriminating_experiment": "MEASURE_ALL_SEAT_POSITIONS_AT_MULTIPLE_VEHICLE_SPEEDS_INCLUDING_STATIONARY_AND_HIGHWAY_ROAD_NOISE",
        "model_assumptions": ["Declared driver/rear seat levels are directly comparable at the same measurement reference",
                               "A tuning not declared validated under road noise is assumed parked-only unless stated otherwise",
                               "This screen evaluates one declared tuning condition, not a full seat/speed coverage matrix"],
        "unresolved": ["Full seat-position and vehicle-speed coverage matrix", "Physical/calibrated in-cabin measurement", "Human production sign-off"],
    }
