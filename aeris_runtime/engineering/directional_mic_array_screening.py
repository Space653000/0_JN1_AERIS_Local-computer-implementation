"""Bounded R068 directional microphone array screening: does declared
sidelobe suppression stay above a declared minimum independent of main-
beam width, and does a claimed unique DOA from a symmetric array geometry
require an explicit ambiguity-resolution mechanism, from supplied scalars
only.

This directly guards against this role's two named failure modes: a narrow
main beam hiding severe sidelobes, and a unique direction-of-arrival claim
from a symmetric array geometry that inherently has a front-back (or other
symmetric) ambiguity unless something explicitly breaks it.
"""
from __future__ import annotations

import math

SCALARS = {"min_acceptable_sidelobe_suppression_db": (0.0, 200.0)}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared directional microphone array screening value outside bounded applicability")


def validate(parameters):
    expected = {"model", "sidelobe_suppression_db", "array_geometry_symmetric", "claimed_unique_doa", "ambiguity_resolved_by_asymmetry_or_extra_sensor"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied directional microphone array screening contract required")
    if parameters["model"] != "SUPPLIED_DIRECTIONAL_MIC_ARRAY_SCREEN":
        raise ValueError("unsupported directional microphone array screening model")
    if isinstance(parameters["sidelobe_suppression_db"], bool) or not isinstance(parameters["sidelobe_suppression_db"], (int, float)) or not math.isfinite(parameters["sidelobe_suppression_db"]):
        raise ValueError("finite declared directional microphone array screening value outside bounded applicability")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    for key in ("array_geometry_symmetric", "claimed_unique_doa", "ambiguity_resolved_by_asymmetry_or_extra_sensor"):
        if not isinstance(parameters[key], bool):
            raise ValueError("boolean directional microphone array screening field required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    sidelobe_suppression = p["sidelobe_suppression_db"]
    symmetric, claim_unique, resolved = p["array_geometry_symmetric"], p["claimed_unique_doa"], p["ambiguity_resolved_by_asymmetry_or_extra_sensor"]
    raw = [
        ("SIDELOBE_SUPPRESSION_ABOVE_MINIMUM", sidelobe_suppression >= p["min_acceptable_sidelobe_suppression_db"],
         "WIDEN_THE_APERTURE_OR_APPLY_SIDELOBE_TAPERING_OR_RELAX_THE_SUPPRESSION_TARGET"),
        ("UNIQUE_DOA_CLAIM_REQUIRES_AMBIGUITY_RESOLUTION", (not claim_unique) or (not symmetric) or resolved,
         "ADD_AN_ASYMMETRIC_ELEMENT_OR_EXTRA_SENSOR_TO_RESOLVE_THE_AMBIGUITY_OR_WITHDRAW_THE_UNIQUE_DOA_CLAIM"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "sidelobe_suppression_db": sidelobe_suppression, "array_geometry_symmetric": symmetric,
        "claimed_unique_doa": claim_unique, "ambiguity_resolved_by_asymmetry_or_extra_sensor": resolved,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["A channel gain/phase mismatch rather than a true steering/sidelobe defect",
                                "A reflected arrival rather than genuine target movement"],
        "next_discriminating_experiment": "MEASURE_THE_FULL_POLAR_PATTERN_INCLUDING_SIDELOBES_AND_VALIDATE_DOA_UNIQUENESS_WITH_A_KNOWN_FRONT_BACK_SOURCE_PAIR",
        "model_assumptions": ["Declared sidelobe suppression is measured relative to the main lobe across the full pattern, not just near it",
                               "A symmetric array geometry is assumed ambiguous unless an explicit resolution mechanism is declared",
                               "This screen evaluates one declared array configuration, not a full steering-angle coverage matrix"],
        "unresolved": ["Full steering-angle and channel-calibration coverage matrix", "Physical/calibrated instrument measurement", "Human production sign-off"],
    }
