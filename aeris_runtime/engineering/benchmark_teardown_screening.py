"""Bounded R086 competitive benchmark/teardown screening: were the compared
products' SPL levels matched, and does a visually inferred topology claim
require electrical validation, from supplied scalars only.

This directly guards against this role's two named failure modes: an
unmatched SPL biasing the benchmark comparison, and teardown appearance
alone being promoted to a validated circuit topology claim.
"""
from __future__ import annotations


def validate(parameters):
    expected = {"model", "spl_matched_across_products", "topology_visually_inferred", "topology_electrically_validated"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied benchmark/teardown screening contract required")
    if parameters["model"] != "SUPPLIED_BENCHMARK_TEARDOWN_SCREEN":
        raise ValueError("unsupported benchmark/teardown screening model")
    for key in ("spl_matched_across_products", "topology_visually_inferred", "topology_electrically_validated"):
        if not isinstance(parameters[key], bool):
            raise ValueError("boolean benchmark/teardown screening field required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    spl_matched = p["spl_matched_across_products"]
    visual, validated = p["topology_visually_inferred"], p["topology_electrically_validated"]
    raw = [
        ("SPL_MATCHED_ACROSS_COMPARED_PRODUCTS", spl_matched,
         "RE_RUN_THE_BENCHMARK_AT_MATCHED_SPL_ACROSS_ALL_COMPARED_PRODUCTS"),
        ("TOPOLOGY_CLAIM_REQUIRES_ELECTRICAL_VALIDATION", (not visual) or validated,
         "ELECTRICALLY_TRACE_AND_VALIDATE_THE_TOPOLOGY_OR_WITHDRAW_THE_TOPOLOGY_CLAIM"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "spl_matched_across_products": spl_matched, "topology_visually_inferred": visual, "topology_electrically_validated": validated,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "visual_appearance_treated_as_validated_topology": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["A test-fixture placement difference rather than a true product performance gap",
                                "A visually similar but electrically distinct topology rather than a shared design"],
        "next_discriminating_experiment": "RE_MEASURE_AT_MATCHED_SPL_AND_ELECTRICALLY_TRACE_THE_SUSPECT_TOPOLOGY_BEFORE_PUBLISHING_A_COMPARISON",
        "model_assumptions": ["Declared SPL-matched flag reflects the actual measurement conditions across all compared products",
                               "A visually inferred topology is assumed unvalidated unless electrical validation is explicitly declared",
                               "This screen evaluates one declared benchmark comparison, not the full product test matrix"],
        "unresolved": ["Full product test-condition matrix", "Physical/calibrated instrument measurement", "Human publication sign-off"],
    }
