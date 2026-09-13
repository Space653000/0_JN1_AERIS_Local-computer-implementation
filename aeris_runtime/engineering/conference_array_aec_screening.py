"""Bounded R067 conference array/AEC screening: does declared off-beam
attenuation stay within a declared bound, and does declared AEC tail
length exceed the declared room path length by a declared margin, from
supplied scalars only.

This directly guards against this role's two named failure modes:
dominant-talker beam steering attenuating an interrupting talker enough to
drop the interruption, and an AEC filter tail shorter than the room's
reverberant path leaving uncancelled echo.
"""
from __future__ import annotations

import math

SCALARS = {
    "max_acceptable_off_beam_attenuation_db": (0.0, 200.0), "aec_tail_length_ms": (0.0, 1e6),
    "room_path_length_ms": (0.0, 1e6), "min_acceptable_aec_tail_margin_ms": (0.0, 1e6),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared conference array/AEC screening value outside bounded applicability")


def validate(parameters):
    expected = {"model", "off_beam_attenuation_db"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied conference array/AEC screening contract required")
    if parameters["model"] != "SUPPLIED_CONFERENCE_ARRAY_AEC_SCREEN":
        raise ValueError("unsupported conference array/AEC screening model")
    if isinstance(parameters["off_beam_attenuation_db"], bool) or not isinstance(parameters["off_beam_attenuation_db"], (int, float)) or not math.isfinite(parameters["off_beam_attenuation_db"]):
        raise ValueError("finite declared conference array/AEC screening value outside bounded applicability")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)


def analyze(parameters):
    validate(parameters)
    p = parameters
    off_beam = p["off_beam_attenuation_db"]
    tail, room_path = p["aec_tail_length_ms"], p["room_path_length_ms"]
    aec_tail_margin = tail - room_path
    raw = [
        ("OFF_BEAM_ATTENUATION_WITHIN_BOUND", off_beam, p["max_acceptable_off_beam_attenuation_db"], "<=",
         "WIDEN_THE_STEERING_BEAM_OR_ADD_AN_INTERRUPTION_DETECTOR_OR_RELAX_THE_ATTENUATION_BOUND"),
        ("AEC_TAIL_EXCEEDS_ROOM_PATH_WITH_MARGIN", aec_tail_margin, p["min_acceptable_aec_tail_margin_ms"], ">=",
         "LENGTHEN_THE_AEC_FILTER_TAIL_OR_TREAT_THE_ROOM_TO_SHORTEN_ITS_REVERBERANT_PATH_OR_RELAX_THE_MARGIN_TARGET"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a <= l if o == "<=" else a >= l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "off_beam_attenuation_db": off_beam, "aec_tail_margin_ms": aec_tail_margin,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Clock drift between capture and reference rather than insufficient AEC filter taps",
                                "Late reflections beyond the modeled room path rather than a true array/steering mismatch"],
        "next_discriminating_experiment": "MEASURE_DOUBLE_TALK_INTERRUPTION_CAPTURE_WITH_AN_ACTIVE_DOMINANT_TALKER_AND_VALIDATE_AEC_CONVERGENCE_AT_THE_MEASURED_ROOM_RT60",
        "model_assumptions": ["Declared off-beam attenuation is the actual steered-array response at the interrupting talker's angle",
                               "Declared room path length is representative of the room's actual reverberant tail",
                               "This screen evaluates one declared operating condition, not a full room/talker coverage matrix"],
        "unresolved": ["Full room and talker-position coverage matrix", "Physical/calibrated instrument measurement", "Human production sign-off"],
    }
