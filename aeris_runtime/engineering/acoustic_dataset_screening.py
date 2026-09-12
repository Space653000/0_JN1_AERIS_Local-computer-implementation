"""Bounded R085 acoustic dataset screening: are mixed sample-rate channels
combined only after explicit resampling, and does the declared duplicate-
source count across dataset splits stay at zero, from supplied scalars
only.

This directly guards against this role's two named failure modes: mixed
sample-rate channels silently combined without resampling, and duplicate
source recordings leaking across dataset splits.
"""
from __future__ import annotations


def validate(parameters):
    expected = {"model", "sample_rates_uniform", "resampling_applied_before_combining", "duplicate_source_count_across_splits"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied acoustic dataset screening contract required")
    if parameters["model"] != "SUPPLIED_ACOUSTIC_DATASET_SCREEN":
        raise ValueError("unsupported acoustic dataset screening model")
    for key in ("sample_rates_uniform", "resampling_applied_before_combining"):
        if not isinstance(parameters[key], bool):
            raise ValueError("boolean acoustic dataset screening field required")
    if isinstance(parameters["duplicate_source_count_across_splits"], bool) or not isinstance(parameters["duplicate_source_count_across_splits"], int) or parameters["duplicate_source_count_across_splits"] < 0:
        raise ValueError("non-negative integer duplicate-source count required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    uniform, resampled = p["sample_rates_uniform"], p["resampling_applied_before_combining"]
    duplicates = p["duplicate_source_count_across_splits"]
    raw = [
        ("SAMPLE_RATES_CONSISTENT_OR_EXPLICITLY_RESAMPLED", uniform or resampled,
         "RESAMPLE_ALL_CHANNELS_TO_A_COMMON_RATE_BEFORE_COMBINING_OR_KEEP_RATES_SEPARATE"),
        ("NO_DUPLICATE_SOURCES_ACROSS_SPLITS", duplicates == 0,
         "REMOVE_DUPLICATE_SOURCE_RECORDINGS_FROM_OVERLAPPING_SPLITS_AND_RE_PARTITION"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "sample_rates_uniform": uniform, "resampling_applied_before_combining": resampled,
        "duplicate_source_count_across_splits": duplicates,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "mixed_rates_silently_combined": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["A metadata labeling error rather than a true sample-rate mismatch",
                                "A near-duplicate rather than the exact same source recording causing the split overlap"],
        "next_discriminating_experiment": "AUDIT_CHANNEL_SAMPLE_RATES_AND_SOURCE_RECORDING_IDS_ACROSS_THE_FULL_DATASET_BEFORE_ANY_TRAINING_RUN",
        "model_assumptions": ["Declared sample-rate-uniform and resampling flags reflect the actual dataset build pipeline, not an assumption",
                               "Declared duplicate-source count is an exact count across splits, not an estimate",
                               "This screen evaluates one declared dataset build state, not the full ingestion pipeline"],
        "unresolved": ["Full ingestion-pipeline audit", "Provenance/license verification", "Human dataset-release sign-off"],
    }
