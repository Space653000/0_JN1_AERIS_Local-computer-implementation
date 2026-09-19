"""Bounded R078 DOE/Monte-Carlo design screening: does a claimed causal
main-effect attribution require a design resolution that actually leaves
main effects unaliased, and does a claimed model-validity require
independent validation rather than merely a small Monte-Carlo standard
error, from supplied scalars only.

This directly guards against this role's two named failure modes: a
confounded (Resolution III) fractional-factorial design being interpreted
causally when its main effects are aliased with two-factor interactions,
and Monte-Carlo sampling precision (a small standard error on the estimate)
being mistaken for the underlying model actually being valid.
"""
from __future__ import annotations

RESOLUTIONS = {3, 4, 5}


def validate(parameters):
    expected = {"model", "design_resolution", "claimed_causal_main_effects", "claimed_model_valid", "model_validated_against_independent_data"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied DOE/Monte-Carlo design screening contract required")
    if parameters["model"] != "SUPPLIED_DOE_MONTE_CARLO_DESIGN_SCREEN":
        raise ValueError("unsupported DOE/Monte-Carlo design screening model")
    if isinstance(parameters["design_resolution"], bool) or parameters["design_resolution"] not in RESOLUTIONS:
        raise ValueError("design resolution must be III, IV or V (supplied as 3, 4 or 5)")
    for key in ("claimed_causal_main_effects", "claimed_model_valid", "model_validated_against_independent_data"):
        if not isinstance(parameters[key], bool):
            raise ValueError("boolean DOE/Monte-Carlo design screening field required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    resolution, causal_claim = p["design_resolution"], p["claimed_causal_main_effects"]
    valid_claim, validated = p["claimed_model_valid"], p["model_validated_against_independent_data"]
    raw = [
        ("MAIN_EFFECTS_CLAIM_REQUIRES_RESOLUTION_IV_OR_HIGHER", (not causal_claim) or resolution >= 4,
         "USE_A_RESOLUTION_IV_OR_HIGHER_DESIGN_OR_WITHDRAW_THE_CAUSAL_MAIN_EFFECT_CLAIM"),
        ("MODEL_VALIDITY_CLAIM_REQUIRES_INDEPENDENT_VALIDATION", (not valid_claim) or validated,
         "VALIDATE_THE_MODEL_AGAINST_INDEPENDENT_DATA_OR_WITHDRAW_THE_MODEL_VALIDITY_CLAIM"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "design_resolution": resolution, "claimed_causal_main_effects": causal_claim,
        "claimed_model_valid": valid_claim, "model_validated_against_independent_data": validated,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "monte_carlo_precision_treated_as_validity": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["A two-factor interaction rather than a genuine main effect at this design resolution",
                                "Batch/run-order drift rather than a true treatment effect"],
        "next_discriminating_experiment": "RUN_A_FOLDOVER_OR_HIGHER_RESOLUTION_DESIGN_TO_DE_ALIAS_THE_SUSPECT_EFFECT_AND_VALIDATE_THE_MODEL_AGAINST_HELD_OUT_DATA",
        "model_assumptions": ["Supplied design resolution and claim/validation flags are exact, not inferred from the raw design matrix",
                               "Resolution III designs alias main effects with two-factor interactions; Resolution IV and above do not",
                               "A small Monte-Carlo standard error reflects sampling precision only, never model correctness on its own"],
        "unresolved": ["Actual design-matrix alias structure verification", "Independent validation dataset provenance", "Physical/production decision authorization"],
    }
