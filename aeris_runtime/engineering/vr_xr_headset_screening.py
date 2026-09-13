"""Bounded R062 VR/XR headset screening: does declared motion-to-sound
latency stay within a declared safe bound, and does declared strap-rubbing
noise stay sufficiently below the declared speech reference level, from
supplied scalars only.

This directly guards against this role's two named failure modes: a
motion-to-sound delay large enough to destabilize the rendered scene, and
mechanical strap-rubbing noise coupling into the capture microphone at a
level close to or above the wanted speech signal.
"""
from __future__ import annotations

import math

SCALARS = {
    "motion_to_sound_latency_ms": (0.0, 1e4), "max_acceptable_motion_to_sound_latency_ms": (1e-9, 1e4),
    "strap_rubbing_noise_rms_pa": (1e-12, 1e3), "speech_reference_rms_pa": (1e-12, 1e3),
    "min_acceptable_strap_rubbing_margin_db": (0.0, 200.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared VR/XR headset screening value outside bounded applicability")


def validate(parameters):
    expected = {"model"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied VR/XR headset screening contract required")
    if parameters["model"] != "SUPPLIED_VR_XR_HEADSET_SCREEN":
        raise ValueError("unsupported VR/XR headset screening model")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)


def analyze(parameters):
    validate(parameters)
    p = parameters
    latency, max_latency = p["motion_to_sound_latency_ms"], p["max_acceptable_motion_to_sound_latency_ms"]
    rubbing, speech = p["strap_rubbing_noise_rms_pa"], p["speech_reference_rms_pa"]
    rubbing_margin_db = 20.0 * math.log10(speech / rubbing)
    raw = [
        ("MOTION_TO_SOUND_LATENCY_WITHIN_BOUND", latency, max_latency, "<=",
         "REDUCE_RENDERER_OR_SPATIALIZATION_LATENCY_OR_RELAX_THE_MOTION_TO_SOUND_BOUND"),
        ("STRAP_RUBBING_MARGIN_ABOVE_MINIMUM", rubbing_margin_db, p["min_acceptable_strap_rubbing_margin_db"], ">=",
         "IMPROVE_STRAP_MECHANICAL_ISOLATION_OR_MICROPHONE_PLACEMENT_OR_RELAX_THE_MARGIN_TARGET"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a <= l if o == "<=" else a >= l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "motion_to_sound_latency_ms": latency, "strap_rubbing_margin_db": rubbing_margin_db,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Tracking timestamp error rather than a true renderer/spatialization delay",
                                "Mechanical strap contact rather than ambient/electrical noise entering the microphone"],
        "next_discriminating_experiment": "MEASURE_MOTION_TO_SOUND_LATENCY_WITH_A_CALIBRATED_TIMESTAMP_REFERENCE_AND_ISOLATE_STRAP_CONTACT_FROM_AMBIENT_NOISE",
        "model_assumptions": ["Declared motion-to-sound latency is the actual end-to-end renderer/spatialization delay, not a tracking-only timestamp",
                               "Declared strap-rubbing and speech reference levels are directly comparable RMS quantities at the same measurement point",
                               "This screen evaluates one declared operating condition, not a full pose/fit distribution"],
        "unresolved": ["Pose-prediction and physical-fit distribution across users", "Physical/calibrated instrument measurement", "Human wear-test and production sign-off"],
    }
