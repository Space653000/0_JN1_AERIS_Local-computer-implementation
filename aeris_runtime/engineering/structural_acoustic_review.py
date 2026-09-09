"""Independent R073 reconstruction of bounded R022 transfer assertions."""
from __future__ import annotations

import math


def _same(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual) == set(expected) and all(_same(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(_same(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, bool) or expected is None:
        return actual is expected
    if isinstance(expected, (int, float)):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12)
    return actual == expected


def review(parameters, candidate):
    from .structural_acoustic import validate

    validate(parameters)
    if not isinstance(candidate, dict):
        raise ValueError("structural/acoustic candidate object required")
    p = parameters
    acceleration_snr = [value / floor for value, floor in zip(p["acceleration_rms_m_s2"], p["acceleration_noise_floor_m_s2"])]
    pressure_snr = [value / floor for value, floor in zip(p["pressure_rms_pa"], p["pressure_noise_floor_pa"])]
    transfer = [pressure / acceleration for pressure, acceleration in zip(p["pressure_rms_pa"], p["acceleration_rms_m_s2"])]
    indices = [index for index in range(len(transfer)) if acceleration_snr[index] >= p["minimum_acceleration_snr_ratio"] and pressure_snr[index] >= p["minimum_pressure_snr_ratio"] and p["coherence"][index] >= p["minimum_coherence"]]
    fraction = len(indices) / len(transfer)
    spread = max(transfer[index] for index in indices) / min(transfer[index] for index in indices) if indices else None
    coherence = min((p["coherence"][index] for index in indices), default=0.0)
    rows = [
        {"id": "IDENTIFIABLE_BAND_FRACTION", "actual": fraction, "limit": p["minimum_identifiable_band_fraction"], "operator": ">=", "passed": fraction >= p["minimum_identifiable_band_fraction"], "on_failure": "ADD_IDENTIFIABLE_BANDS_OR_WITHHOLD_TRANSFER_INTERPRETATION"},
        {"id": "TRANSFER_SPREAD", "actual": spread, "limit": p["maximum_transfer_spread_ratio"], "operator": "<=", "passed": spread is not None and spread <= p["maximum_transfer_spread_ratio"], "on_failure": "SEPARATE_MODES_PATHS_OR_OPERATING_CONDITIONS"},
        {"id": "IDENTIFIABLE_COHERENCE", "actual": coherence, "limit": p["minimum_coherence"], "operator": ">=", "passed": coherence >= p["minimum_coherence"], "on_failure": "IMPROVE_SYNCHRONIZATION_SNR_OR_PATH_EXCITATION"},
        {"id": "FREQUENCY_ALIGNMENT", "actual": p["frequency_alignment_bound_hz"], "limit": p["maximum_frequency_alignment_bound_hz"], "operator": "<=", "passed": p["frequency_alignment_bound_hz"] <= p["maximum_frequency_alignment_bound_hz"], "on_failure": "REALIGN_STRUCTURAL_AND_ACOUSTIC_SPECTRA"},
    ]
    expected = {
        "acceleration_snr_ratio": acceleration_snr, "pressure_snr_ratio": pressure_snr,
        "transfer_pa_per_m_s2": transfer, "identifiable_band_indices": indices,
        "identifiable_band_fraction": fraction, "transfer_spread_ratio": spread, "checks": rows,
        "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "causal_path_verified": False, "radiation_efficiency_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Mount-stiffness change rather than source-amplitude change", "Electrical pickup rather than mechanically radiated sound", "Acoustic loading rather than structural damping change"],
        "next_discriminating_experiment": "REPEAT_SYNCHRONIZED_ACCELERATION_PRESSURE_BANDS_WITH_MOUNT_AND_ELECTRICAL_PICKUP_CONTROLS",
        "model_assumptions": ["Supplied band RMS values share time/frequency alignment", "Pressure-to-acceleration ratio is a descriptive transfer metric only", "Magnitude-squared coherence gates identifiability but does not establish causation"],
        "unresolved": ["Transfer direction and causal path", "Mode shapes, radiation efficiency and boundary loading", "Sensor calibration, physical repetition and qualified Human acceptance"],
    }
    if set(candidate) != set(expected):
        raise ValueError("exact structural/acoustic assertions required")
    differences = [{"field": key, "asserted": candidate[key], "expected": value} for key, value in expected.items() if not _same(candidate[key], value)]
    return {
        "domain": "structural-acoustic-path", "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT",
        "disagreements": differences,
        "observations": {"causality_scope": "not established by coherence", "unresolved": "mode shapes and path direction"},
        "human_approval": False, "role_l3_awarded": False,
        "scope": "bounded synchronized band transfer-identifiability report consistency only",
    }
