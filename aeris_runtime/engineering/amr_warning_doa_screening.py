"""Bounded R064 AMR warning/DOA screening: does declared warning-to-motor-
noise margin stay above a declared minimum, and does the robot's
displacement during one DOA update interval stay within a declared
position-uncertainty bound, from supplied scalars only.

This directly guards against this role's two named failure modes: a safety
warning masked by drive-motor noise, and a fixed-source direction-of-
arrival assumption breaking down because the robot moved too far during one
DOA update interval.
"""
from __future__ import annotations

import math

SCALARS = {
    "min_acceptable_warning_margin_db": (0.0, 200.0), "robot_velocity_m_s": (0.0, 1e3),
    "doa_update_interval_s": (1e-9, 1e6), "max_acceptable_position_uncertainty_m": (1e-9, 1e6),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared AMR warning/DOA screening value outside bounded applicability")


def validate(parameters):
    expected = {"model", "warning_level_db", "drive_motor_noise_db"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied AMR warning/DOA screening contract required")
    if parameters["model"] != "SUPPLIED_AMR_WARNING_DOA_SCREEN":
        raise ValueError("unsupported AMR warning/DOA screening model")
    for key in ("warning_level_db", "drive_motor_noise_db"):
        if isinstance(parameters[key], bool) or not isinstance(parameters[key], (int, float)) or not math.isfinite(parameters[key]):
            raise ValueError("finite declared AMR warning/DOA screening value outside bounded applicability")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)


def analyze(parameters):
    validate(parameters)
    p = parameters
    warning, motor = p["warning_level_db"], p["drive_motor_noise_db"]
    velocity, interval = p["robot_velocity_m_s"], p["doa_update_interval_s"]
    warning_margin = warning - motor
    displacement = velocity * interval
    raw = [
        ("WARNING_MARGIN_ABOVE_MOTOR_NOISE", warning_margin, p["min_acceptable_warning_margin_db"], ">=",
         "INCREASE_WARNING_LEVEL_OR_REDUCE_MOTOR_NOISE_OR_RELAX_THE_MARGIN_TARGET"),
        ("DOA_DISPLACEMENT_WITHIN_POSITION_UNCERTAINTY", displacement, p["max_acceptable_position_uncertainty_m"], "<=",
         "INCREASE_DOA_UPDATE_RATE_OR_REDUCE_ROBOT_VELOCITY_OR_RELAX_THE_POSITION_UNCERTAINTY_BOUND"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a >= l if o == ">=" else a <= l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "warning_margin_db": warning_margin, "doa_update_displacement_m": displacement,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Chassis vibration coupling rather than true capsule/electrical noise",
                                "Relative motion during the update interval rather than a clock/synchronization fault"],
        "next_discriminating_experiment": "MEASURE_WARNING_AUDIBILITY_AGAINST_MOTOR_NOISE_AT_MAXIMUM_DRIVE_LOAD_AND_VALIDATE_DOA_TRACKING_AT_MAXIMUM_RATED_VELOCITY",
        "model_assumptions": ["Declared warning and motor-noise levels are directly comparable at the same measurement reference",
                               "Robot velocity is constant across one DOA update interval",
                               "This screen evaluates one declared operating condition, not a full velocity/load coverage matrix"],
        "unresolved": ["Full velocity/load coverage matrix", "Physical/calibrated instrument measurement", "Human production sign-off"],
    }
