"""Bounded R092 instrument-sequence safety screening: does a planned dry-run
stimulus sequence stay within declared fixture safety limits, from supplied
scalars only.

This is deliberately NOT a physical instrument run: it never claims a
reading was acquired and never executes real IO. It answers a narrower,
honest question -- "given a declared stimulus amplitude, per-step duration,
step count and fixture safety limits, does the *planned* sequence clear
those limits before any physical execution is authorized" -- guarding
against exactly the two failure modes this role's profile names: a dry-run
result mistaken for a physical reading, and a planned stimulus that would
exceed the fixture's safety limit if it were ever run.
"""
from __future__ import annotations

import math

SCALARS = {
    "planned_stimulus_amplitude": (0.0, 1e6), "max_fixture_stimulus_amplitude": (1e-12, 1e6),
    "planned_step_duration_s": (1e-9, 1e6), "max_fixture_step_duration_s": (1e-9, 1e6),
    "max_cumulative_duration_s": (1e-9, 1e9),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared instrument-sequence safety value outside bounded applicability")


def validate(parameters):
    expected = {"model", "planned_step_count"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied instrument-sequence safety screening contract required")
    if parameters["model"] != "SUPPLIED_INSTRUMENT_STIMULUS_SAFETY_SCREEN":
        raise ValueError("unsupported instrument-sequence safety screening model")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    if isinstance(parameters["planned_step_count"], bool) or not isinstance(parameters["planned_step_count"], int) or parameters["planned_step_count"] <= 0:
        raise ValueError("positive integer planned step count required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    amplitude, max_amplitude = p["planned_stimulus_amplitude"], p["max_fixture_stimulus_amplitude"]
    duration, max_duration = p["planned_step_duration_s"], p["max_fixture_step_duration_s"]
    count, max_cumulative = p["planned_step_count"], p["max_cumulative_duration_s"]
    cumulative_duration = duration * count
    raw = [
        ("STIMULUS_AMPLITUDE_WITHIN_FIXTURE_LIMIT", amplitude, max_amplitude, "<=",
         "REDUCE_PLANNED_STIMULUS_AMPLITUDE_OR_USE_A_HIGHER_RATED_FIXTURE"),
        ("STEP_DURATION_WITHIN_FIXTURE_LIMIT", duration, max_duration, "<=",
         "REDUCE_PLANNED_STEP_DURATION_OR_USE_A_HIGHER_RATED_FIXTURE"),
        ("CUMULATIVE_DURATION_WITHIN_BUDGET", cumulative_duration, max_cumulative, "<=",
         "REDUCE_STEP_COUNT_OR_STEP_DURATION_OR_RELAX_CUMULATIVE_BUDGET"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a <= l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "cumulative_duration_s": cumulative_duration,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "dry_run_only": True, "physical_execution_performed": False,
        "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Declared fixture limit stale relative to the actual installed fixture rather than the planned sequence being unsafe",
                                "Planned amplitude/duration units mismatched against the fixture's rated units rather than a true overstress"],
        "next_discriminating_experiment": "VERIFY_FIXTURE_NAMEPLATE_RATING_AND_UNIT_CONVENTION_BEFORE_ANY_PHYSICAL_EXECUTION_AUTHORIZATION",
        "model_assumptions": ["Declared fixture limits are the actual, current, authoritative safety limits for the fixture that will be used",
                               "Stimulus amplitude and duration are constant across every planned step",
                               "No physical instrument IO occurs as part of this screening"],
        "unresolved": ["Actual fixture nameplate/calibration verification", "Explicit Human IO authorization", "Physical instrument execution and acquisition provenance"],
    }
