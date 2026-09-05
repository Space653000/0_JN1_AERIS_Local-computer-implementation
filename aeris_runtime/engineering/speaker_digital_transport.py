"""Bounded R014 I2S/TDM format, clock and buffer transport screening."""
from __future__ import annotations

import math


SCALARS = {
    "sample_rate_hz": (8000.0, 768000.0), "slot_width_bits": (8, 64),
    "word_length_bits": (8, 64), "slots_per_frame": (1, 64),
    "bit_clock_hz": (1.0, 1e9), "bit_clock_relative_tolerance": (0.0, 0.1),
    "frame_sync_hz": (1.0, 1e6), "frame_sync_relative_tolerance": (0.0, 0.1),
    "buffer_capacity_frames": (1, 1e9), "worst_case_service_interval_ms": (0.0, 1e6),
    "minimum_buffer_margin_frames": (0, 1e9), "maximum_buffer_latency_ms": (0.0, 1e6),
    "expected_channel_count": (1, 64),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared transport value outside bounded applicability")


def validate(parameters):
    expected = set(SCALARS) | {"model", "active_slot_indices", "packing"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied I2S/TDM transport contract required")
    if parameters["model"] != "SUPPLIED_I2S_TDM_TRANSPORT":
        raise ValueError("unsupported digital transport model")
    if parameters["packing"] not in {"I2S_ONE_BIT_DELAY", "LEFT_JUSTIFIED", "TDM_LEFT_JUSTIFIED"}:
        raise ValueError("unsupported or ambiguous serial packing")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    for key in ("slot_width_bits", "word_length_bits", "slots_per_frame", "buffer_capacity_frames", "minimum_buffer_margin_frames", "expected_channel_count"):
        if not isinstance(parameters[key], int):
            raise ValueError("integer transport field required: " + key)
    slots = parameters["active_slot_indices"]
    if (not isinstance(slots, list) or len(slots) != parameters["expected_channel_count"]
            or any(isinstance(item, bool) or not isinstance(item, int) for item in slots)):
        raise ValueError("exact integer active-slot map required")
    if len(set(slots)) != len(slots) or any(item < 0 or item >= parameters["slots_per_frame"] for item in slots):
        raise ValueError("active slots must be unique and inside the TDM frame")


def _values(parameters):
    p = parameters
    expected_bclk = p["sample_rate_hz"] * p["slot_width_bits"] * p["slots_per_frame"]
    bclk_error = abs(p["bit_clock_hz"] / expected_bclk - 1.0)
    fs_error = abs(p["frame_sync_hz"] / p["sample_rate_hz"] - 1.0)
    service_frames = p["sample_rate_hz"] * p["worst_case_service_interval_ms"] / 1000.0
    buffer_margin = p["buffer_capacity_frames"] - service_frames
    buffer_latency = 1000.0 * p["buffer_capacity_frames"] / p["sample_rate_hz"]
    return expected_bclk, bclk_error, fs_error, service_frames, buffer_margin, buffer_latency


def analyze(parameters):
    validate(parameters)
    p = parameters
    expected_bclk, bclk_error, fs_error, service_frames, buffer_margin, buffer_latency = _values(p)
    raw = [
        ("WORD_FITS_SLOT", p["word_length_bits"], p["slot_width_bits"], "<=", "INCREASE_SLOT_WIDTH_OR_REDUCE_WORD_LENGTH"),
        ("BIT_CLOCK_RELATION", bclk_error, p["bit_clock_relative_tolerance"], "<=", "RECONCILE_SAMPLE_RATE_SLOT_WIDTH_AND_TDM_SLOT_COUNT"),
        ("FRAME_SYNC_RELATION", fs_error, p["frame_sync_relative_tolerance"], "<=", "RECONCILE_FRAME_SYNC_AND_SAMPLE_RATE"),
        ("SERVICE_BUFFER_MARGIN", buffer_margin, p["minimum_buffer_margin_frames"], ">=", "INCREASE_BUFFER_OR_REDUCE_WORST_CASE_SERVICE_INTERVAL"),
        ("BUFFER_LATENCY", buffer_latency, p["maximum_buffer_latency_ms"], "<=", "REDUCE_BUFFER_CAPACITY_OR_REVISE_LATENCY_BUDGET"),
        ("ACTIVE_SLOT_COVERAGE", len(p["active_slot_indices"]), p["expected_channel_count"], "==", "REPAIR_CHANNEL_TO_SLOT_MAPPING"),
    ]
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a <= l if o == "<=" else a >= l if o == ">=" else a == l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {
        "expected_bit_clock_hz": expected_bclk, "bit_clock_relative_error": bclk_error,
        "frame_sync_relative_error": fs_error, "service_interval_frames": service_frames,
        "buffer_margin_frames": buffer_margin, "buffer_latency_ms": buffer_latency,
        "active_slot_indices": list(p["active_slot_indices"]), "packing": p["packing"], "checks": checks,
        "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "glitch_free_playback_verified": False, "physical_interface_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Clock-domain slip rather than DSP overload", "Serial packing mismatch rather than acoustic fault", "Scheduler service tail rather than average processing latency"],
        "next_discriminating_experiment": "CAPTURE_BCLK_FRAME_SYNC_DATA_AND_BUFFER_WATERMARKS_WITH_DECLARED_PACKING",
        "model_assumptions": ["One frame is produced per declared sample period", "Worst-case service interval is a supplied deterministic bound", "No electrical timing, jitter spectrum or driver execution is measured"],
        "unresolved": ["Electrical setup/hold and jitter", "DMA/driver scheduling tails and underrun telemetry", "Physical playback continuity and qualified Human acceptance"],
    }
