"""Bounded R065 quadruped capture screening: does declared footfall
headroom margin stay above a declared minimum, and does declared body
orientation stay within a declared fixed-beam tolerance, from supplied
scalars only.

This directly guards against this role's two named failure modes: footfall
impulses saturating the capture path, and body orientation drifting far
enough that a fixed beamforming direction assumption no longer holds.
"""
from __future__ import annotations

import math

SCALARS = {
    "min_acceptable_headroom_margin_db": (0.0, 200.0), "body_orientation_deg": (0.0, 180.0),
    "max_acceptable_beam_orientation_tolerance_deg": (0.0, 180.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared quadruped capture screening value outside bounded applicability")


def validate(parameters):
    expected = {"model", "footfall_peak_level_pa", "capture_headroom_pa"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied quadruped capture screening contract required")
    if parameters["model"] != "SUPPLIED_QUADRUPED_CAPTURE_SCREEN":
        raise ValueError("unsupported quadruped capture screening model")
    for key in ("footfall_peak_level_pa", "capture_headroom_pa"):
        if isinstance(parameters[key], bool) or not isinstance(parameters[key], (int, float)) or not math.isfinite(parameters[key]) or parameters[key] <= 0:
            raise ValueError("positive finite declared quadruped capture screening value required")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)


def analyze(parameters):
    validate(parameters)
    p = parameters
    footfall, headroom = p["footfall_peak_level_pa"], p["capture_headroom_pa"]
    orientation = p["body_orientation_deg"]
    headroom_margin_db = 20.0 * math.log10(headroom / footfall)
    raw = [
        ("FOOTFALL_HEADROOM_MARGIN_ABOVE_MINIMUM", headroom_margin_db, p["min_acceptable_headroom_margin_db"], ">=",
         "REDUCE_FOOTFALL_COUPLING_OR_INCREASE_CAPTURE_HEADROOM_OR_RELAX_THE_MARGIN_TARGET"),
        ("BODY_ORIENTATION_WITHIN_FIXED_BEAM_TOLERANCE", orientation, p["max_acceptable_beam_orientation_tolerance_deg"], "<=",
         "STEER_OR_RE_ESTIMATE_THE_BEAM_FOR_CURRENT_BODY_ORIENTATION_OR_RELAX_THE_TOLERANCE"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a >= l if o == ">=" else a <= l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "footfall_headroom_margin_db": headroom_margin_db, "body_orientation_deg": orientation,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Mount/structural impact coupling rather than wind or ambient noise",
                                "A gait-mode transition rather than a true noise-reduction instability"],
        "next_discriminating_experiment": "MEASURE_FOOTFALL_PEAK_LEVELS_ACROSS_GAIT_MODES_AND_VALIDATE_BEAM_STEERING_ACROSS_THE_FULL_BODY_ORIENTATION_RANGE",
        "model_assumptions": ["Declared footfall and headroom levels are directly comparable peak quantities at the same measurement point",
                               "Declared body orientation is the actual deviation from the beam's assumed nominal orientation",
                               "This screen evaluates one declared operating condition, not a full gait/orientation coverage matrix"],
        "unresolved": ["Full gait-mode and orientation coverage matrix", "Physical/calibrated instrument measurement", "Human production sign-off"],
    }
