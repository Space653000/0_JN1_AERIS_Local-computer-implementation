"""Independent Decimal recomputation of the bounded R011 port assertions."""
from __future__ import annotations

import math
from decimal import Decimal, localcontext


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
    from .ported_alignment import validate

    validate(parameters)
    if not isinstance(candidate, dict):
        raise ValueError("ported alignment candidate object required")
    p = parameters
    with localcontext() as context:
        context.prec = 60
        d = {key: Decimal(str(value)) for key, value in p.items() if key != "model"}
        pi = Decimal(str(math.pi))

        def tuning(c, area, volume, length):
            return c / (2 * pi) * (area / volume / length).sqrt()

        effective = d["physical_length_m"] + d["end_correction_m"]
        nominal = tuning(d["sound_speed_m_s"], d["port_area_m2"], d["cavity_volume_m3"], effective)
        interval = [
            tuning(d["sound_speed_lower_m_s"], d["port_area_lower_m2"], d["cavity_volume_upper_m3"], d["effective_length_upper_m"]),
            tuning(d["sound_speed_upper_m_s"], d["port_area_upper_m2"], d["cavity_volume_lower_m3"], d["effective_length_lower_m"]),
        ]
        velocity = d["volume_velocity_peak_m3_s"] / d["port_area_m2"]
        velocity_upper = d["volume_velocity_upper_m3_s"] / d["port_area_lower_m2"]
        longitudinal = d["sound_speed_lower_m_s"] / (2 * d["effective_length_upper_m"])
        mode_ratio = longitudinal / d["analysis_max_hz"]
        geometry = d["largest_dimension_m"] * d["analysis_max_hz"] / d["sound_speed_lower_m_s"]
    interval_f = list(map(float, interval))
    rows = [
        {"id": "TUNING_INTERVAL", "actual": interval_f,
         "limit": [p["minimum_tuning_hz"], p["maximum_tuning_hz"]],
         "passed": interval_f[0] >= p["minimum_tuning_hz"] and interval_f[1] <= p["maximum_tuning_hz"],
         "on_failure": "REVISE_PORT_AREA_EFFECTIVE_LENGTH_OR_CAVITY_BOUNDS"},
        {"id": "PORT_VELOCITY", "actual": float(velocity_upper), "limit": p["maximum_port_velocity_m_s"],
         "passed": float(velocity_upper) <= p["maximum_port_velocity_m_s"],
         "on_failure": "INCREASE_PORT_AREA_OR_REDUCE_VOLUME_VELOCITY"},
        {"id": "LONGITUDINAL_MODE_SEPARATION", "actual": float(mode_ratio), "limit": p["minimum_longitudinal_mode_ratio"],
         "passed": float(mode_ratio) >= p["minimum_longitudinal_mode_ratio"],
         "on_failure": "SHORTEN_PORT_OR_LIMIT_ANALYSIS_BAND_AND_MODEL_RESONANCE"},
        {"id": "LUMPED_GEOMETRY_VALIDITY", "actual": float(geometry), "limit": p["maximum_dimension_wavelength_ratio"],
         "passed": float(geometry) <= p["maximum_dimension_wavelength_ratio"],
         "on_failure": "ESCALATE_TO_SPATIALLY_VALID_PORT_OR_WAVEGUIDE_MODEL"},
    ]
    expected = {
        "effective_length_m": float(effective), "tuning_hz": float(nominal), "tuning_interval_hz": interval_f,
        "port_velocity_m_s": float(velocity), "port_velocity_upper_m_s": float(velocity_upper),
        "longitudinal_mode_lower_hz": float(longitudinal), "longitudinal_mode_ratio": float(mode_ratio),
        "dimension_wavelength_ratio": float(geometry), "checks": rows,
        "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "chuffing_verified": False, "waveguide_directivity_verified": False, "physical_measurement_verified": False,
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
    if set(candidate) != set(expected):
        raise ValueError("exact ported alignment assertions required")
    differences = [
        {"field": key, "asserted": candidate[key], "expected": value}
        for key, value in expected.items() if not _same(candidate[key], value)
    ]
    return {
        "domain": "speaker-port-lumped",
        "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT",
        "disagreements": differences,
        "observations": {
            "interval_scope": "independent supplied geometry and sound-speed bounds, not calibrated distributions",
            "unresolved": "Actual turbulence, leakage, end correction, boundary loading and higher modes",
        },
        "human_approval": False,
        "role_l3_awarded": False,
        "scope": "bounded port tuning, velocity and lumped-validity report consistency only",
    }
