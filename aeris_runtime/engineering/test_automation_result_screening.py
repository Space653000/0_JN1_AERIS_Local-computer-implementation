"""Bounded R091 deterministic test-automation result screening: does a
claimed pass disclose any retries it took, and is it backed by an explicit
pass signal rather than the test process merely staying alive, from
supplied scalars only.

This directly guards against this role's two named failure modes: a retry
hiding a persistent failure (an eventual pass reported without disclosing
the attempts that failed first), and a test process being alive at the end
of a run mistaken for the test having actually passed.
"""
from __future__ import annotations


def validate(parameters):
    expected = {"model", "attempt_count", "final_attempt_passed", "retries_disclosed", "explicit_pass_signal_received"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied test-automation result screening contract required")
    if parameters["model"] != "SUPPLIED_TEST_AUTOMATION_RESULT_SCREEN":
        raise ValueError("unsupported test-automation result screening model")
    if isinstance(parameters["attempt_count"], bool) or not isinstance(parameters["attempt_count"], int) or parameters["attempt_count"] < 1:
        raise ValueError("positive integer attempt count required")
    for key in ("final_attempt_passed", "retries_disclosed", "explicit_pass_signal_received"):
        if not isinstance(parameters[key], bool):
            raise ValueError("boolean test-automation result field required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    attempts, disclosed, signal = p["attempt_count"], p["retries_disclosed"], p["explicit_pass_signal_received"]
    raw = [
        ("RETRIES_ARE_DISCLOSED_NOT_HIDDEN", attempts <= 1 or disclosed,
         "DISCLOSE_THE_RETRY_COUNT_AND_EACH_FAILED_ATTEMPT_RATHER_THAN_REPORTING_ONLY_THE_FINAL_PASS"),
        ("PASS_SIGNAL_IS_EXPLICIT_NOT_PROCESS_ALIVE", signal,
         "REQUIRE_AN_EXPLICIT_ASSERTION_OR_PASS_SIGNAL_RATHER_THAN_INFERRING_PASS_FROM_THE_PROCESS_STAYING_ALIVE"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "attempt_count": attempts, "final_attempt_passed": p["final_attempt_passed"],
        "retries_disclosed": disclosed, "explicit_pass_signal_received": signal,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "process_alive_treated_as_pass": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["Fixture state leakage between attempts rather than a true product regression",
                                "A race condition in the test harness rather than genuinely intermittent hardware"],
        "next_discriminating_experiment": "RERUN_WITH_FIXTURE_STATE_RESET_BETWEEN_ATTEMPTS_AND_AN_EXPLICIT_ASSERTION_BASED_PASS_SIGNAL",
        "model_assumptions": ["Supplied attempt count, disclosure flag and pass-signal flag are exact, not inferred from logs",
                               "A single attempt has no retry to disclose", "This screen evaluates one test result claim only, not the full automation run"],
        "unresolved": ["Root cause of any retried failure", "Full automation-run resource/timeout budget", "Physical/production release authorization"],
    }
