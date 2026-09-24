"""Bounded R100 next-experiment safety screening: does a proposed next
experiment point stay inside a declared safe region and represent
sufficiently new information relative to prior points, from supplied
scalars only.

This directly guards against this role's two named failure modes: an
optimizer extrapolating a proposed point outside the declared safe region,
and a point close enough to an already-tested one being wrongly counted as
new informative coverage. The caller supplies the already-computed distance
from the proposed point to its nearest previously tested point (this skill
does not itself search or store a point history); it only screens the one
proposed step.
"""
from __future__ import annotations

import math

SCALARS = {
    "min_new_information_distance": (0.0, 1e9), "nearest_previous_point_distance": (0.0, 1e9),
}


def _number(value, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("finite declared next-experiment safety value outside bounded applicability")
    if low is not None and not low <= value <= (high if high is not None else value):
        raise ValueError("finite declared next-experiment safety value outside bounded applicability")


def validate(parameters):
    expected = {"model", "proposed_point", "safe_region_min", "safe_region_max"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied next-experiment safety screening contract required")
    if parameters["model"] != "SUPPLIED_NEXT_EXPERIMENT_SAFETY_SCREEN":
        raise ValueError("unsupported next-experiment safety screening model")
    for key in ("proposed_point", "safe_region_min", "safe_region_max"):
        if isinstance(parameters[key], bool) or not isinstance(parameters[key], (int, float)) or not math.isfinite(parameters[key]):
            raise ValueError("finite declared next-experiment safety value outside bounded applicability")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    if parameters["safe_region_max"] <= parameters["safe_region_min"]:
        raise ValueError("safe region maximum must exceed safe region minimum")


def analyze(parameters):
    validate(parameters)
    p = parameters
    point, lo, hi = p["proposed_point"], p["safe_region_min"], p["safe_region_max"]
    distance, min_distance = p["nearest_previous_point_distance"], p["min_new_information_distance"]
    raw = [
        ("PROPOSED_POINT_WITHIN_SAFE_REGION", lo <= point <= hi,
         "CLIP_OR_REPLAN_THE_PROPOSED_POINT_INSIDE_THE_DECLARED_SAFE_REGION"),
        ("SUFFICIENTLY_NEW_INFORMATION", distance >= min_distance,
         "PROPOSE_A_POINT_FARTHER_FROM_ALREADY_TESTED_COVERAGE_OR_RELAX_THE_NEW_INFORMATION_DISTANCE"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "proposed_point": point, "safe_region_min": lo, "safe_region_max": hi,
        "nearest_previous_point_distance": distance, "min_new_information_distance": min_distance,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "risk_gate_overridden": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Measurement noise at the proposed point rather than a true improvement over prior coverage",
                                "An unexplored factor interaction rather than the proposed point itself being uninformative"],
        "next_discriminating_experiment": "REPLICATE_THE_PROPOSED_POINT_OR_PROBE_THE_NEAREST_UNEXPLORED_INTERACTION_BEFORE_ACCEPTING_A_SINGLE_STEP",
        "model_assumptions": ["Supplied safe region bounds are the actual, current, authoritative safe operating region",
                               "Caller has already computed the true nearest-previous-point distance; this screen does not search point history",
                               "This screen evaluates one proposed step only, not a full experiment sequence"],
        "unresolved": ["Full point-history search/deduplication", "Risk gate authority beyond this single-step screen", "Physical execution and Human authorization"],
    }
