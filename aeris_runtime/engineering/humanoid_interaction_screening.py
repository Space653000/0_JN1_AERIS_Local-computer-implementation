"""Bounded R066 humanoid interaction screening: does declared user-
interruption-to-residual-self-echo margin stay above a declared minimum,
and does declared joint noise during head-tracking motion stay
sufficiently below the user speech reference, from supplied scalars only.

This directly guards against this role's two named failure modes: robot
self-speech (residual echo after AEC) masking a user's barge-in
interruption, and joint/actuator noise that follows head-tracking motion
contaminating voice activity detection.
"""
from __future__ import annotations

import math

SCALARS = {"min_acceptable_interruption_margin_db": (0.0, 200.0), "min_acceptable_joint_noise_margin_db": (0.0, 200.0)}


def _positive(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError("positive finite declared humanoid interaction screening value required")


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared humanoid interaction screening value outside bounded applicability")


def validate(parameters):
    expected = {"model", "residual_self_echo_rms_pa", "user_interruption_rms_pa", "joint_noise_during_tracking_rms_pa", "user_speech_reference_rms_pa"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied humanoid interaction screening contract required")
    if parameters["model"] != "SUPPLIED_HUMANOID_INTERACTION_SCREEN":
        raise ValueError("unsupported humanoid interaction screening model")
    for key in ("residual_self_echo_rms_pa", "user_interruption_rms_pa", "joint_noise_during_tracking_rms_pa", "user_speech_reference_rms_pa"):
        _positive(parameters[key])
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)


def analyze(parameters):
    validate(parameters)
    p = parameters
    echo, interruption = p["residual_self_echo_rms_pa"], p["user_interruption_rms_pa"]
    joint_noise, speech = p["joint_noise_during_tracking_rms_pa"], p["user_speech_reference_rms_pa"]
    interruption_margin_db = 20.0 * math.log10(interruption / echo)
    joint_noise_margin_db = 20.0 * math.log10(speech / joint_noise)
    raw = [
        ("INTERRUPTION_ABOVE_RESIDUAL_SELF_ECHO", interruption_margin_db, p["min_acceptable_interruption_margin_db"], ">=",
         "IMPROVE_AEC_RESIDUAL_SUPPRESSION_OR_LOWER_ROBOT_PLAYBACK_LEVEL_OR_RELAX_THE_MARGIN_TARGET"),
        ("JOINT_NOISE_BELOW_SPEECH_DURING_TRACKING", joint_noise_margin_db, p["min_acceptable_joint_noise_margin_db"], ">=",
         "IMPROVE_ACTUATOR_ACOUSTIC_ISOLATION_OR_GATE_VAD_DURING_TRACKING_MOTION_OR_RELAX_THE_MARGIN_TARGET"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a >= l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "interruption_margin_db": interruption_margin_db, "joint_noise_margin_db": joint_noise_margin_db,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["A self-echo acoustic path change rather than a true speech-detector error",
                                "An actuator harmonic rather than genuine human voice activity"],
        "next_discriminating_experiment": "MEASURE_BARGE_IN_DETECTION_DURING_ACTIVE_ROBOT_PLAYBACK_AND_JOINT_NOISE_ACROSS_THE_FULL_HEAD_TRACKING_RANGE",
        "model_assumptions": ["Declared echo/interruption and joint-noise/speech levels are directly comparable RMS quantities at the same measurement point",
                               "Residual self-echo is measured after AEC, not the raw playback level",
                               "This screen evaluates one declared operating condition, not a full conversational/motion coverage matrix"],
        "unresolved": ["Full conversational-turn and head-tracking-motion coverage matrix", "Physical/calibrated instrument measurement", "Human production sign-off"],
    }
