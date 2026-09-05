"""Bounded R022 structural/acoustic transfer identifiability screen."""
from __future__ import annotations

import math


ARRAYS = {"frequency_hz", "acceleration_rms_m_s2", "pressure_rms_pa", "coherence", "acceleration_noise_floor_m_s2", "pressure_noise_floor_pa"}
SCALARS = {
    "minimum_acceleration_snr_ratio": (1.0, 1e12), "minimum_pressure_snr_ratio": (1.0, 1e12),
    "minimum_coherence": (0.0, 1.0), "minimum_identifiable_band_fraction": (0.0, 1.0),
    "maximum_transfer_spread_ratio": (1.0, 1e12), "frequency_alignment_bound_hz": (0.0, 1e6),
    "maximum_frequency_alignment_bound_hz": (0.0, 1e6),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared structural/acoustic value outside bounded applicability")


def validate(parameters):
    expected = ARRAYS | set(SCALARS) | {"model"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied structural/acoustic band contract required")
    if parameters["model"] != "SUPPLIED_STRUCTURAL_ACOUSTIC_BANDS":
        raise ValueError("unsupported structural/acoustic model")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    arrays = [parameters[key] for key in ARRAYS]
    if any(not isinstance(values, list) for values in arrays) or not 3 <= len(parameters["frequency_hz"]) <= 2048:
        raise ValueError("bounded aligned structural/acoustic arrays required")
    count = len(parameters["frequency_hz"])
    if any(len(values) != count for values in arrays):
        raise ValueError("all structural/acoustic arrays must align")
    for frequency in parameters["frequency_hz"]:
        _number(frequency, 1.0, 100000.0)
    if any(right <= left for left, right in zip(parameters["frequency_hz"], parameters["frequency_hz"][1:])):
        raise ValueError("strictly increasing unique frequency samples required")
    for key in ("acceleration_rms_m_s2", "pressure_rms_pa"):
        for value in parameters[key]:
            _number(value, 1e-18, 1e12)
    for key in ("acceleration_noise_floor_m_s2", "pressure_noise_floor_pa"):
        for value in parameters[key]:
            _number(value, 1e-18, 1e12)
    for value in parameters["coherence"]:
        _number(value, 0.0, 1.0)


def analyze(parameters):
    validate(parameters)
    p = parameters
    acceleration_snr = [value / floor for value, floor in zip(p["acceleration_rms_m_s2"], p["acceleration_noise_floor_m_s2"])]
    pressure_snr = [value / floor for value, floor in zip(p["pressure_rms_pa"], p["pressure_noise_floor_pa"])]
    transfer = [pressure / acceleration for pressure, acceleration in zip(p["pressure_rms_pa"], p["acceleration_rms_m_s2"])]
    indices = [index for index in range(len(transfer)) if acceleration_snr[index] >= p["minimum_acceleration_snr_ratio"] and pressure_snr[index] >= p["minimum_pressure_snr_ratio"] and p["coherence"][index] >= p["minimum_coherence"]]
    fraction = len(indices) / len(transfer)
    spread = max(transfer[index] for index in indices) / min(transfer[index] for index in indices) if indices else None
    minimum_identifiable_coherence = min((p["coherence"][index] for index in indices), default=0.0)
    checks = [
        {"id": "IDENTIFIABLE_BAND_FRACTION", "actual": fraction, "limit": p["minimum_identifiable_band_fraction"], "operator": ">=", "passed": fraction >= p["minimum_identifiable_band_fraction"], "on_failure": "ADD_IDENTIFIABLE_BANDS_OR_WITHHOLD_TRANSFER_INTERPRETATION"},
        {"id": "TRANSFER_SPREAD", "actual": spread, "limit": p["maximum_transfer_spread_ratio"], "operator": "<=", "passed": spread is not None and spread <= p["maximum_transfer_spread_ratio"], "on_failure": "SEPARATE_MODES_PATHS_OR_OPERATING_CONDITIONS"},
        {"id": "IDENTIFIABLE_COHERENCE", "actual": minimum_identifiable_coherence, "limit": p["minimum_coherence"], "operator": ">=", "passed": minimum_identifiable_coherence >= p["minimum_coherence"], "on_failure": "IMPROVE_SYNCHRONIZATION_SNR_OR_PATH_EXCITATION"},
        {"id": "FREQUENCY_ALIGNMENT", "actual": p["frequency_alignment_bound_hz"], "limit": p["maximum_frequency_alignment_bound_hz"], "operator": "<=", "passed": p["frequency_alignment_bound_hz"] <= p["maximum_frequency_alignment_bound_hz"], "on_failure": "REALIGN_STRUCTURAL_AND_ACOUSTIC_SPECTRA"},
    ]
    return {
        "acceleration_snr_ratio": acceleration_snr,
        "pressure_snr_ratio": pressure_snr,
        "transfer_pa_per_m_s2": transfer,
        "identifiable_band_indices": indices,
        "identifiable_band_fraction": fraction,
        "transfer_spread_ratio": spread,
        "checks": checks,
        "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "causal_path_verified": False,
        "radiation_efficiency_verified": False,
        "physical_measurement_verified": False,
        "counter_hypotheses": [
            "Mount-stiffness change rather than source-amplitude change",
            "Electrical pickup rather than mechanically radiated sound",
            "Acoustic loading rather than structural damping change",
        ],
        "next_discriminating_experiment": "REPEAT_SYNCHRONIZED_ACCELERATION_PRESSURE_BANDS_WITH_MOUNT_AND_ELECTRICAL_PICKUP_CONTROLS",
        "model_assumptions": [
            "Supplied band RMS values share time/frequency alignment",
            "Pressure-to-acceleration ratio is a descriptive transfer metric only",
            "Magnitude-squared coherence gates identifiability but does not establish causation",
        ],
        "unresolved": [
            "Transfer direction and causal path",
            "Mode shapes, radiation efficiency and boundary loading",
            "Sensor calibration, physical repetition and qualified Human acceptance",
        ],
    }
