"""Bounded R083 codec/transport screening: does declared jitter-buffer
margin over network jitter stay above a declared minimum, and does the
declared consecutive packet-loss burst length stay within the concealment
algorithm's declared capability, from supplied scalars only.

This directly guards against this role's two named failure modes: reducing
the jitter buffer far enough to produce audible dropouts, and scoring
packet loss only by its average rate while ignoring burst structure (a
burst long enough to exceed concealment capability degrades quality far
more than the same total loss spread out as isolated single-packet drops).
"""
from __future__ import annotations

import math

SCALARS = {"min_acceptable_buffer_margin_ms": (0.0, 1e5)}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared codec/transport screening value outside bounded applicability")


def validate(parameters):
    expected = {"model", "jitter_buffer_ms", "network_jitter_ms", "max_consecutive_loss_burst_packets", "max_acceptable_loss_burst_packets"} | set(SCALARS)
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied codec/transport screening contract required")
    if parameters["model"] != "SUPPLIED_CODEC_TRANSPORT_SCREEN":
        raise ValueError("unsupported codec/transport screening model")
    for key in ("jitter_buffer_ms", "network_jitter_ms"):
        if isinstance(parameters[key], bool) or not isinstance(parameters[key], (int, float)) or not math.isfinite(parameters[key]) or parameters[key] < 0:
            raise ValueError("non-negative finite declared codec/transport screening value required")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    for key in ("max_consecutive_loss_burst_packets", "max_acceptable_loss_burst_packets"):
        if isinstance(parameters[key], bool) or not isinstance(parameters[key], int) or parameters[key] < 0:
            raise ValueError("non-negative integer packet-burst count required")


def analyze(parameters):
    validate(parameters)
    p = parameters
    buffer_ms, jitter_ms = p["jitter_buffer_ms"], p["network_jitter_ms"]
    burst, max_burst = p["max_consecutive_loss_burst_packets"], p["max_acceptable_loss_burst_packets"]
    buffer_margin_ms = buffer_ms - jitter_ms
    raw = [
        ("BUFFER_MARGIN_ABOVE_MINIMUM", buffer_margin_ms >= p["min_acceptable_buffer_margin_ms"],
         "INCREASE_JITTER_BUFFER_SIZE_OR_REDUCE_NETWORK_JITTER_OR_RELAX_THE_MARGIN_TARGET"),
        ("LOSS_BURST_WITHIN_CONCEALMENT_CAPABILITY", burst <= max_burst,
         "IMPROVE_LOSS_CONCEALMENT_BURST_HANDLING_OR_REDUCE_NETWORK_BURST_LOSS_OR_RELAX_THE_BURST_TARGET"),
    ]
    checks = [{"id": i, "passed": ok, "on_failure": f} for i, ok, f in raw]
    return {
        "buffer_margin_ms": buffer_margin_ms, "max_consecutive_loss_burst_packets": burst,
        "checks": checks, "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "average_loss_rate_treated_as_sufficient": False, "physical_measurement_verified": False, "professional_tool_verified": False,
        "counter_hypotheses": ["A transient network condition rather than a persistent jitter/buffer mismatch",
                                "A concealment-algorithm limitation rather than the burst length itself being unusual"],
        "next_discriminating_experiment": "MEASURE_DROPOUT_RATE_AT_THE_DECLARED_BUFFER_SIZE_UNDER_REPRESENTATIVE_NETWORK_JITTER_AND_VALIDATE_CONCEALMENT_AT_THE_DECLARED_BURST_LENGTH",
        "model_assumptions": ["Declared jitter-buffer and network-jitter values are directly comparable time quantities",
                               "Declared consecutive-loss-burst length is the actual worst observed burst, not an average loss rate",
                               "This screen evaluates one declared operating condition, not a full network-condition coverage matrix"],
        "unresolved": ["Full network-condition coverage matrix", "Physical/production instrument measurement", "Human production sign-off"],
    }
