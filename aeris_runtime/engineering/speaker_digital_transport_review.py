"""Independent R032 reconstruction of bounded R014 transport assertions."""
from __future__ import annotations

import math


def _same(actual, expected):
    if isinstance(expected, dict): return isinstance(actual, dict) and set(actual) == set(expected) and all(_same(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list): return isinstance(actual, list) and len(actual) == len(expected) and all(_same(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, bool) or expected is None: return actual is expected
    if isinstance(expected, (int, float)): return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12)
    return actual == expected


def review(parameters, candidate):
    from .speaker_digital_transport import validate, _values
    validate(parameters)
    if not isinstance(candidate, dict): raise ValueError("digital-transport candidate object required")
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
    rows = [{"id": i, "actual": a, "limit": l, "operator": o, "passed": a <= l if o == "<=" else a >= l if o == ">=" else a == l, "on_failure": f} for i, a, l, o, f in raw]
    expected = {
        "expected_bit_clock_hz": expected_bclk, "bit_clock_relative_error": bclk_error,
        "frame_sync_relative_error": fs_error, "service_interval_frames": service_frames,
        "buffer_margin_frames": buffer_margin, "buffer_latency_ms": buffer_latency,
        "active_slot_indices": list(p["active_slot_indices"]), "packing": p["packing"], "checks": rows,
        "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "glitch_free_playback_verified": False, "physical_interface_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Clock-domain slip rather than DSP overload", "Serial packing mismatch rather than acoustic fault", "Scheduler service tail rather than average processing latency"],
        "next_discriminating_experiment": "CAPTURE_BCLK_FRAME_SYNC_DATA_AND_BUFFER_WATERMARKS_WITH_DECLARED_PACKING",
        "model_assumptions": ["One frame is produced per declared sample period", "Worst-case service interval is a supplied deterministic bound", "No electrical timing, jitter spectrum or driver execution is measured"],
        "unresolved": ["Electrical setup/hold and jitter", "DMA/driver scheduling tails and underrun telemetry", "Physical playback continuity and qualified Human acceptance"],
    }
    if set(candidate) != set(expected): raise ValueError("exact digital-transport assertions required")
    differences = [{"field": k, "asserted": candidate[k], "expected": v} for k, v in expected.items() if not _same(candidate[k], v)]
    return {"domain": "speaker-digital-transport", "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT", "disagreements": differences,
            "observations": {"clock_scope": "declared arithmetic relations only", "unresolved": "electrical timing and real underrun telemetry"},
            "human_approval": False, "role_l3_awarded": False, "scope": "bounded serial-audio transport report consistency only"}
