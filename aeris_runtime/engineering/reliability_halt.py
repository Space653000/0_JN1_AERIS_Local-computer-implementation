"""Bounded R096 HALT/reliability screening: exact one-sided binomial upper
bound on failure probability from supplied trial/failure counts only.

This is deliberately NOT accelerated-life-testing analysis: it performs no
Arrhenius/temperature-acceleration extrapolation and claims none. It answers
a narrower, honest question -- "given N units stressed and K failures
observed, what is the statistical upper bound on the true failure
probability at the stated confidence, and does that clear a declared
acceptance threshold" -- the same exact binomial method already used by
aeris_runtime.engineering.governance.reliability, applied here as a bounded
role-domain decision with a disposition, not a bare statistic.
"""
from __future__ import annotations

import math

from scipy import stats

SCALARS = {
    "trials": (1, 1_000_000), "failures": (0, 1_000_000),
    "confidence": (0.0, 0.999999), "max_acceptable_failure_probability": (0.0, 1.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared HALT screening value outside bounded applicability")


def validate(parameters):
    expected = set(SCALARS) | {"model"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied HALT binomial screening contract required")
    if parameters["model"] != "SUPPLIED_HALT_BINOMIAL_SCREEN":
        raise ValueError("unsupported HALT screening model")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    if not isinstance(parameters["trials"], int) or not isinstance(parameters["failures"], int):
        raise ValueError("integer trials/failures required")
    if parameters["failures"] > parameters["trials"]:
        raise ValueError("failures cannot exceed trials")


def analyze(parameters):
    validate(parameters)
    p = parameters
    trials, failures, confidence = p["trials"], p["failures"], p["confidence"]
    upper = 1.0 if failures == trials else float(stats.beta.ppf(confidence, failures + 1, trials - failures))
    observed_fraction = failures / trials
    raw = [
        ("UPPER_BOUND_WITHIN_ACCEPTANCE", upper, p["max_acceptable_failure_probability"], "<=",
         "REDUCE_FAILURE_RATE_OR_INCREASE_SAMPLE_SIZE_OR_RELAX_ACCEPTANCE_TARGET"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a <= l if o == "<=" else a >= l if o == ">=" else a == l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "observed_failure_fraction": observed_fraction, "one_sided_upper_failure_probability": upper,
        "confidence": confidence, "max_acceptable_failure_probability": p["max_acceptable_failure_probability"],
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "accelerated_life_extrapolation_performed": False, "temperature_acceleration_modeled": False,
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Sampling variation at small trial count rather than a true elevated failure rate",
                                "Screening-stage failure mode not representative of field stress profile"],
        "next_discriminating_experiment": "INCREASE_SAMPLE_SIZE_OR_RUN_DECLARED_ACCELERATED_LIFE_MODEL_WITH_ACTIVATION_ENERGY_EVIDENCE",
        "model_assumptions": ["Independent identical Bernoulli trials", "Supplied trial/failure counts are exact, not estimated",
                               "No accelerated-life (e.g. Arrhenius) extrapolation is performed"],
        "unresolved": ["Failure-mode root cause", "Field-use stress-profile equivalence", "Physical HALT chamber execution and qualified Human acceptance"],
    }
