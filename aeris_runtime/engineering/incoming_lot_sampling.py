"""Bounded R095 incoming-lot sampling screening: separates supplier
incoming-quality sampling risk from assembly/test-system variation, from
supplied scalars only.

This directly guards against this role's two named failure modes: a
supplier certificate of conformance mistaken for measured incoming
inspection data, and a small sample used to accept a lot whose true defect
rate has actually shifted. The exact one-sided binomial upper bound on the
lot's true nonconforming fraction is the same tested method already used by
aeris_runtime.engineering.governance.reliability and reliability_halt.py --
a small sample naturally produces a wide (large) upper bound, so it is
penalized honestly through interval width rather than needing a separate
sample-size-adequacy formula.
"""
from __future__ import annotations

import math

from scipy import stats

SCALARS = {
    "confidence": (0.0, 0.999999), "max_acceptable_lot_fraction_nonconforming": (0.0, 1.0),
}
MEASURED = "MEASURED_INCOMING_INSPECTION"
SOURCE_KINDS = {MEASURED, "SUPPLIER_CERTIFICATE_ONLY"}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared incoming-lot sampling value outside bounded applicability")


def validate(parameters):
    expected = {"model", "source_kind", "sample_size", "observed_nonconforming"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied incoming-lot sampling screening contract required")
    if parameters["model"] != "SUPPLIED_INCOMING_LOT_SAMPLING_SCREEN":
        raise ValueError("unsupported incoming-lot sampling screening model")
    if parameters["source_kind"] not in SOURCE_KINDS:
        raise ValueError("unknown incoming-lot data source kind")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    for key in ("sample_size", "observed_nonconforming"):
        if isinstance(parameters[key], bool) or not isinstance(parameters[key], int) or parameters[key] < 0:
            raise ValueError("non-negative integer sample counts required")
    if parameters["sample_size"] <= 0:
        raise ValueError("positive sample size required")
    if parameters["observed_nonconforming"] > parameters["sample_size"]:
        raise ValueError("observed nonconforming count cannot exceed sample size")


def analyze(parameters):
    validate(parameters)
    p = parameters
    source_kind, sample_size, nonconforming, confidence = p["source_kind"], p["sample_size"], p["observed_nonconforming"], p["confidence"]
    upper = 1.0 if nonconforming == sample_size else float(stats.beta.ppf(confidence, nonconforming + 1, sample_size - nonconforming))
    observed_fraction = nonconforming / sample_size
    raw = [
        ("SOURCE_IS_MEASURED_INCOMING_INSPECTION", source_kind == MEASURED,
         "OBTAIN_MEASURED_INCOMING_INSPECTION_DATA_NOT_A_SUPPLIER_CERTIFICATE"),
        ("UPPER_BOUND_WITHIN_ACCEPTABLE_FRACTION", upper <= p["max_acceptable_lot_fraction_nonconforming"],
         "INCREASE_SAMPLE_SIZE_OR_REDUCE_OBSERVED_NONCONFORMING_OR_RELAX_ACCEPTANCE_TARGET"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "observed_fraction_nonconforming": observed_fraction, "one_sided_upper_fraction_nonconforming": upper,
        "confidence": confidence, "max_acceptable_lot_fraction_nonconforming": p["max_acceptable_lot_fraction_nonconforming"],
        "source_kind": source_kind,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "assembly_test_variation_separated": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Assembly/test-system variation rather than a true supplier lot shift",
                                "Sampling variation at small sample size rather than a true elevated nonconforming rate"],
        "next_discriminating_experiment": "INCREASE_INCOMING_SAMPLE_SIZE_WITH_MEASURED_INSPECTION_AND_SEPARATE_ASSEMBLY_TEST_SYSTEM_VARIATION_STUDY",
        "model_assumptions": ["Sample units are independent identical Bernoulli trials from the lot", "Supplied sample/nonconforming counts are exact, not estimated",
                               "This screen does not itself separate assembly/test-system variation from incoming lot variation"],
        "unresolved": ["Assembly/test-system variation decomposition", "Supplier certificate authenticity", "Physical/calibrated incoming inspection and Human disposition"],
    }
