"""Bounded R084 audio ML evaluation screening: does the declared train/test
source-recording overlap count stay at zero, and does a claimed production-
robustness require declared production-representative validation rather
than a synthetic-only accuracy figure, from supplied scalars only.

This directly guards against this role's two named failure modes: the same
source recording appearing in both train and test splits (leakage that
inflates accuracy), and synthetic test accuracy being presented as
production robustness without validation on production-representative
data.
"""
from __future__ import annotations


def validate(parameters):
    expected = {"model", "train_test_overlap_count", "claimed_production_robust", "production_validated"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied audio ML evaluation screening contract required")
    if parameters["model"] != "SUPPLIED_AUDIO_ML_EVALUATION_SCREEN":
        raise ValueError("unsupported audio ML evaluation screening model")
    if isinstance(parameters["train_test_overlap_count"], bool) or not isinstance(parameters["train_test_overlap_count"], int) or parameters["train_test_overlap_count"] < 0:
        raise ValueError("non-negative integer train/test overlap count required")
    for key in ("claimed_production_robust", "production_validated"):
        if not isinstance(parameters[key], bool):
            raise ValueError("boolean audio ML evaluation screening field required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    overlap, claim_robust, validated = p["train_test_overlap_count"], p["claimed_production_robust"], p["production_validated"]
    raw = [
        ("NO_TRAIN_TEST_SOURCE_OVERLAP", overlap == 0,
         "REMOVE_OVERLAPPING_SOURCE_RECORDINGS_FROM_TRAIN_OR_TEST_AND_RE_EVALUATE"),
        ("PRODUCTION_ROBUSTNESS_CLAIM_REQUIRES_VALIDATION", (not claim_robust) or validated,
         "VALIDATE_ON_PRODUCTION_REPRESENTATIVE_DATA_OR_WITHDRAW_THE_PRODUCTION_ROBUSTNESS_CLAIM"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "train_test_overlap_count": overlap, "claimed_production_robust": claim_robust, "production_validated": validated,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "synthetic_accuracy_treated_as_production_robustness": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["A near-duplicate rather than the exact same source recording causing the overlap",
                                "A distribution-shift-specific failure rather than a general lack of production robustness"],
        "next_discriminating_experiment": "AUDIT_SOURCE_RECORDING_IDS_ACROSS_SPLITS_AND_EVALUATE_ON_A_HELD_OUT_PRODUCTION_REPRESENTATIVE_DATASET",
        "model_assumptions": ["Declared train/test overlap count is an exact count of shared source recordings, not an estimate",
                               "Production-representative validation means evaluation on data drawn from the actual deployment distribution, not additional synthetic data",
                               "This screen evaluates one declared evaluation claim, not the full model training pipeline"],
        "unresolved": ["Full dataset provenance audit", "Distribution-shift characterization", "Human model-release sign-off"],
    }
