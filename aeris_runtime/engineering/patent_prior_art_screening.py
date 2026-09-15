"""Bounded R087 patent/prior-art screening: does a claimed novelty verdict
require element-by-element claim mapping rather than keyword similarity
alone, and is the correct date type (priority, not publication) used for
prior-art comparison, from supplied scalars only.

This directly guards against this role's two named failure modes: keyword
similarity being presented as a novelty verdict, and a priority date being
confused with a publication date.
"""
from __future__ import annotations

DATE_TYPES = {"PRIORITY_DATE", "PUBLICATION_DATE"}


def validate(parameters):
    expected = {"model", "novelty_verdict_claimed", "claim_element_mapping_performed", "date_type_used"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied patent/prior-art screening contract required")
    if parameters["model"] != "SUPPLIED_PATENT_PRIOR_ART_SCREEN":
        raise ValueError("unsupported patent/prior-art screening model")
    for key in ("novelty_verdict_claimed", "claim_element_mapping_performed"):
        if not isinstance(parameters[key], bool):
            raise ValueError("boolean patent/prior-art screening field required")
    if parameters["date_type_used"] not in DATE_TYPES:
        raise ValueError("unknown date type; must be PRIORITY_DATE or PUBLICATION_DATE")


def analyze(parameters):
    validate(parameters)
    p = parameters
    novelty_claimed, mapped = p["novelty_verdict_claimed"], p["claim_element_mapping_performed"]
    date_type = p["date_type_used"]
    raw = [
        ("NOVELTY_VERDICT_REQUIRES_CLAIM_ELEMENT_MAPPING", (not novelty_claimed) or mapped,
         "PERFORM_ELEMENT_BY_ELEMENT_CLAIM_MAPPING_OR_WITHDRAW_THE_NOVELTY_VERDICT"),
        ("CORRECT_DATE_TYPE_USED_FOR_PRIOR_ART_COMPARISON", date_type == "PRIORITY_DATE",
         "RE_DERIVE_THE_COMPARISON_USING_THE_PRIORITY_DATE_NOT_THE_PUBLICATION_DATE"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "novelty_verdict_claimed": novelty_claimed, "claim_element_mapping_performed": mapped, "date_type_used": date_type,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "keyword_similarity_treated_as_novelty_verdict": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["A shared field-of-art vocabulary rather than a true overlapping claim element",
                                "A continuation/divisional filing date rather than the true earliest priority date"],
        "next_discriminating_experiment": "PERFORM_A_FULL_ELEMENT_BY_ELEMENT_CLAIM_CHART_AGAINST_THE_VERIFIED_PRIORITY_DATE_BEFORE_ANY_NOVELTY_VERDICT",
        "model_assumptions": ["Declared claim-element-mapping flag reflects an actual element-by-element analysis, not a keyword match",
                               "Declared date type is the correctly identified date for this comparison, not assumed",
                               "This screen evaluates one declared prior-art comparison, not a full freedom-to-operate analysis"],
        "unresolved": ["Full claim chart and element-by-element analysis", "Jurisdiction/status verification", "Human legal sign-off"],
    }
