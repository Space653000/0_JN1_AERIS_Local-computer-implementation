"""Bounded R093 factory EOL/QC screening: process capability (Cpk) against a
declared spec, and percent gage R&R against total variation, from supplied
scalars only.

This is deliberately NOT a physical measurement-system study: it performs no
ANOVA gage R&R decomposition from raw part/operator/trial data and claims
none. It answers a narrower, honest question -- "given a declared process
mean/std against declared spec limits, and a declared gage repeatability/
reproducibility standard deviation, does the process capability and percent
gage R&R clear declared acceptance thresholds" -- using the textbook Cpk
formula and the standard AIAG MSA quadrature definition of %GRR (gage std
over total std, where total std combines part and gage variation in
quadrature), applied here as a bounded role-domain decision with a
disposition, not a bare statistic.
"""
from __future__ import annotations

import math

SCALARS = {
    "process_std": (1e-12, 1e6), "gage_std": (0.0, 1e6),
    "min_acceptable_cpk": (0.0, 100.0), "max_acceptable_grr_percent": (0.0, 100.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared EOL capability screening value outside bounded applicability")


def validate(parameters):
    expected = {"model", "process_mean", "usl", "lsl"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied EOL capability screening contract required")
    if parameters["model"] != "SUPPLIED_EOL_CAPABILITY_SCREEN":
        raise ValueError("unsupported EOL capability screening model")
    for key in ("process_mean", "usl", "lsl"):
        if isinstance(parameters[key], bool) or not isinstance(parameters[key], (int, float)) or not math.isfinite(parameters[key]):
            raise ValueError("finite declared EOL capability screening value outside bounded applicability")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    if parameters["usl"] <= parameters["lsl"]:
        raise ValueError("upper spec limit must exceed lower spec limit")


def analyze(parameters):
    validate(parameters)
    p = parameters
    mean, std, usl, lsl, gage_std = p["process_mean"], p["process_std"], p["usl"], p["lsl"], p["gage_std"]
    cpu = (usl - mean) / (3 * std)
    cpl = (mean - lsl) / (3 * std)
    cpk = min(cpu, cpl)
    total_std = math.sqrt(std ** 2 + gage_std ** 2)
    grr_percent = 100.0 * gage_std / total_std if total_std > 0 else 0.0
    raw = [
        ("CPK_MEETS_MINIMUM", cpk, p["min_acceptable_cpk"], ">=",
         "TIGHTEN_PROCESS_VARIATION_OR_RECENTER_MEAN_OR_RELAX_SPEC_LIMITS"),
        ("GRR_WITHIN_MAXIMUM", grr_percent, p["max_acceptable_grr_percent"], "<=",
         "IMPROVE_GAGE_REPEATABILITY_REPRODUCIBILITY_OR_RELAX_GRR_TARGET"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a >= l if o == ">=" else a <= l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "cpu": cpu, "cpl": cpl, "cpk": cpk, "total_std": total_std, "grr_percent": grr_percent,
        "min_acceptable_cpk": p["min_acceptable_cpk"], "max_acceptable_grr_percent": p["max_acceptable_grr_percent"],
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "measurement_system_study_performed": False, "eol_test_limit_set": False,
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Pilot-sample mean/std unrepresentative of long-run production rather than a true capability shift",
                                "Declared gage variation not representative of the actual measurement system under production conditions"],
        "next_discriminating_experiment": "RUN_FULL_ANOVA_GAGE_RR_STUDY_WITH_MULTIPLE_OPERATORS_PARTS_AND_TRIALS_AND_LONG_RUN_PROCESS_SAMPLE",
        "model_assumptions": ["Process output is normally distributed with the supplied mean and standard deviation",
                               "Supplied process/gage standard deviations are exact, not estimated from a specific sample",
                               "Part and gage variation combine in quadrature (AIAG MSA total-variation convention)"],
        "unresolved": ["Long-run process stability", "Actual gage R&R study execution", "Physical EOL test-limit authorization and Human production sign-off"],
    }
