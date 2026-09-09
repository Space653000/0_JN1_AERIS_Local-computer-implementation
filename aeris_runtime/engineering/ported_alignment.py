"""Ideal lumped Helmholtz port decision with supplied independent bounds."""
from __future__ import annotations

import math


FIELDS = {
    "sound_speed_m_s": (100.0, 1000.0),
    "sound_speed_lower_m_s": (100.0, 1000.0),
    "sound_speed_upper_m_s": (100.0, 1000.0),
    "cavity_volume_m3": (1e-9, 100.0),
    "cavity_volume_lower_m3": (1e-9, 100.0),
    "cavity_volume_upper_m3": (1e-9, 100.0),
    "port_area_m2": (1e-9, 10.0),
    "port_area_lower_m2": (1e-9, 10.0),
    "port_area_upper_m2": (1e-9, 10.0),
    "physical_length_m": (1e-6, 100.0),
    "end_correction_m": (0.0, 100.0),
    "effective_length_lower_m": (1e-6, 100.0),
    "effective_length_upper_m": (1e-6, 100.0),
    "volume_velocity_peak_m3_s": (0.0, 1000.0),
    "volume_velocity_upper_m3_s": (0.0, 1000.0),
    "minimum_tuning_hz": (0.1, 20000.0),
    "maximum_tuning_hz": (0.1, 20000.0),
    "maximum_port_velocity_m_s": (1e-9, 1000.0),
    "analysis_max_hz": (0.1, 200000.0),
    "minimum_longitudinal_mode_ratio": (1.0, 1000.0),
    "largest_dimension_m": (1e-6, 100.0),
    "maximum_dimension_wavelength_ratio": (1e-6, 1.0),
}


def validate(parameters):
    if not isinstance(parameters, dict) or set(parameters) != set(FIELDS) | {"model"}:
        raise ValueError("exact ideal lumped Helmholtz SI contract required")
    if parameters["model"] != "IDEAL_LUMPED_HELMHOLTZ_PORT":
        raise ValueError("unsupported port model")
    for key, (low, high) in FIELDS.items():
        value = parameters[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError("finite declared parameter outside bounded applicability: " + key)
    for nominal, lower, upper in (
        ("sound_speed_m_s", "sound_speed_lower_m_s", "sound_speed_upper_m_s"),
        ("cavity_volume_m3", "cavity_volume_lower_m3", "cavity_volume_upper_m3"),
        ("port_area_m2", "port_area_lower_m2", "port_area_upper_m2"),
    ):
        if not parameters[lower] <= parameters[nominal] <= parameters[upper]:
            raise ValueError("nominal must lie inside supplied independent bounds")
    effective = parameters["physical_length_m"] + parameters["end_correction_m"]
    if not parameters["effective_length_lower_m"] <= effective <= parameters["effective_length_upper_m"]:
        raise ValueError("physical plus end-correction length must lie inside effective-length bounds")
    if parameters["volume_velocity_peak_m3_s"] > parameters["volume_velocity_upper_m3_s"]:
        raise ValueError("volume-velocity upper bound must contain nominal")
    if parameters["minimum_tuning_hz"] > parameters["maximum_tuning_hz"]:
        raise ValueError("ordered tuning requirement required")


def _tuning(c, area, volume, length):
    return c / (2 * math.pi) * math.sqrt(area / (volume * length))


def analyze(parameters):
    validate(parameters)
    p = parameters
    effective = p["physical_length_m"] + p["end_correction_m"]
    tuning = _tuning(p["sound_speed_m_s"], p["port_area_m2"], p["cavity_volume_m3"], effective)
    tuning_interval = [
        _tuning(p["sound_speed_lower_m_s"], p["port_area_lower_m2"], p["cavity_volume_upper_m3"], p["effective_length_upper_m"]),
        _tuning(p["sound_speed_upper_m_s"], p["port_area_upper_m2"], p["cavity_volume_lower_m3"], p["effective_length_lower_m"]),
    ]
    velocity = p["volume_velocity_peak_m3_s"] / p["port_area_m2"]
    velocity_upper = p["volume_velocity_upper_m3_s"] / p["port_area_lower_m2"]
    longitudinal_lower = p["sound_speed_lower_m_s"] / (2 * p["effective_length_upper_m"])
    longitudinal_ratio = longitudinal_lower / p["analysis_max_hz"]
    geometry_ratio = p["largest_dimension_m"] * p["analysis_max_hz"] / p["sound_speed_lower_m_s"]
    checks = [
        {"id": "TUNING_INTERVAL", "actual": tuning_interval,
         "limit": [p["minimum_tuning_hz"], p["maximum_tuning_hz"]],
         "passed": tuning_interval[0] >= p["minimum_tuning_hz"] and tuning_interval[1] <= p["maximum_tuning_hz"],
         "on_failure": "REVISE_PORT_AREA_EFFECTIVE_LENGTH_OR_CAVITY_BOUNDS"},
        {"id": "PORT_VELOCITY", "actual": velocity_upper, "limit": p["maximum_port_velocity_m_s"],
         "passed": velocity_upper <= p["maximum_port_velocity_m_s"],
         "on_failure": "INCREASE_PORT_AREA_OR_REDUCE_VOLUME_VELOCITY"},
        {"id": "LONGITUDINAL_MODE_SEPARATION", "actual": longitudinal_ratio,
         "limit": p["minimum_longitudinal_mode_ratio"],
         "passed": longitudinal_ratio >= p["minimum_longitudinal_mode_ratio"],
         "on_failure": "SHORTEN_PORT_OR_LIMIT_ANALYSIS_BAND_AND_MODEL_RESONANCE"},
        {"id": "LUMPED_GEOMETRY_VALIDITY", "actual": geometry_ratio,
         "limit": p["maximum_dimension_wavelength_ratio"],
         "passed": geometry_ratio <= p["maximum_dimension_wavelength_ratio"],
         "on_failure": "ESCALATE_TO_SPATIALLY_VALID_PORT_OR_WAVEGUIDE_MODEL"},
    ]
    return {
        "effective_length_m": effective,
        "tuning_hz": tuning,
        "tuning_interval_hz": tuning_interval,
        "port_velocity_m_s": velocity,
        "port_velocity_upper_m_s": velocity_upper,
        "longitudinal_mode_lower_hz": longitudinal_lower,
        "longitudinal_mode_ratio": longitudinal_ratio,
        "dimension_wavelength_ratio": geometry_ratio,
        "checks": checks,
        "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "chuffing_verified": False,
        "waveguide_directivity_verified": False,
        "physical_measurement_verified": False,
        "counter_hypotheses": [
            "Turbulent port flow rather than driver harmonic distortion",
            "Boundary loading or end-correction error rather than incorrect physical port length",
        ],
        "next_discriminating_experiment": "MEASURE_PORT_PRESSURE_AND_VOLUME_VELOCITY_WITH_BOUNDARY_CONFIGURATION_RECORDED",
        "model_assumptions": [
            "Ideal lumped Helmholtz cavity and port with supplied effective-length bounds",
            "Incompressible mean volume velocity divided by area is only a screening velocity",
            "First longitudinal port mode uses a half-wave screening estimate",
            "Independent supplied bounds are not calibrated probability distributions",
        ],
        "unresolved": [
            "Actual end correction, leakage, damping and turbulent transition",
            "Higher port modes, baffle loading and waveguide directivity",
            "Calibrated acoustic measurement and qualified Human acceptance",
        ],
    }
