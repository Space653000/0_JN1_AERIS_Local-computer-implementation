"""Bounded R088 research hypothesis screening: does a claimed replication
require an actual independent replication rather than a citation count,
and is raw-data availability always explicitly disclosed rather than
hidden behind an abstract summary, from supplied scalars only.

This directly guards against this role's two named failure modes: citation
count being treated as replication, and unavailable raw data being hidden
by an abstract summary instead of disclosed.
"""
from __future__ import annotations


def validate(parameters):
    expected = {"model", "replication_claimed", "independent_replication_performed", "raw_data_availability_disclosed"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied research hypothesis screening contract required")
    if parameters["model"] != "SUPPLIED_RESEARCH_HYPOTHESIS_SCREEN":
        raise ValueError("unsupported research hypothesis screening model")
    for key in ("replication_claimed", "independent_replication_performed", "raw_data_availability_disclosed"):
        if not isinstance(parameters[key], bool):
            raise ValueError("boolean research hypothesis screening field required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    replication_claimed, replicated = p["replication_claimed"], p["independent_replication_performed"]
    disclosed = p["raw_data_availability_disclosed"]
    raw = [
        ("REPLICATION_CLAIM_REQUIRES_INDEPENDENT_REPLICATION", (not replication_claimed) or replicated,
         "PERFORM_AN_ACTUAL_INDEPENDENT_REPLICATION_OR_WITHDRAW_THE_REPLICATION_CLAIM"),
        ("RAW_DATA_AVAILABILITY_MUST_BE_DISCLOSED", disclosed,
         "EXPLICITLY_DISCLOSE_RAW_DATA_AVAILABILITY_RATHER_THAN_RELYING_ON_AN_ABSTRACT_SUMMARY"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "replication_claimed": replication_claimed, "independent_replication_performed": replicated,
        "raw_data_availability_disclosed": disclosed,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "citation_count_treated_as_replication": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Frequent citation for context or critique rather than confirmatory replication",
                                "A methodological difference rather than the original result itself being unreplicated"],
        "next_discriminating_experiment": "IDENTIFY_AND_RUN_AN_ACTUAL_INDEPENDENT_REPLICATION_ATTEMPT_AND_EXPLICITLY_STATE_RAW_DATA_AVAILABILITY_BEFORE_ANY_HYPOTHESIS_ACCEPTANCE",
        "model_assumptions": ["Declared independent-replication flag reflects an actual re-run study, not a citation count",
                               "Declared raw-data-disclosure flag reflects an explicit statement, not an assumption from an abstract",
                               "This screen evaluates one declared hypothesis claim, not the full literature review"],
        "unresolved": ["Full literature review and citation-context analysis", "Raw-data access verification", "Human peer-review sign-off"],
    }
