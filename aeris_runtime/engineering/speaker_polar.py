"""Bounded validation of supplied absolute horizontal speaker polar samples."""
from __future__ import annotations

import math


SCALARS = {
    "supplied_on_axis_reference_db": (-120.0, 200.0),
    "level_uncertainty_db": (0.0, 40.0),
    "minimum_coverage_deg": (1.0, 360.0),
    "maximum_angular_gap_deg": (0.1, 180.0),
    "maximum_on_axis_reference_error_db": (0.0, 60.0),
    "minimum_edge_attenuation_db": (-60.0, 120.0),
    "maximum_symmetry_error_db": (0.0, 60.0),
    "angle_alignment_bound_deg": (0.0, 180.0),
    "maximum_angle_alignment_bound_deg": (0.0, 180.0),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared polar value outside bounded applicability")


def validate(parameters):
    expected = set(SCALARS) | {"model", "angles_deg", "levels_db", "normalization_mode"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied absolute polar contract required")
    if parameters["model"] != "SUPPLIED_HORIZONTAL_POLAR_ABSOLUTE" or parameters["normalization_mode"] != "ABSOLUTE_NOT_PEAK_NORMALIZED":
        raise ValueError("only supplied non-peak-normalized horizontal polar samples are supported")
    for key, bounds in SCALARS.items():
        _number(parameters[key], *bounds)
    angles = parameters["angles_deg"]
    levels = parameters["levels_db"]
    if not isinstance(angles, list) or not isinstance(levels, list) or not 3 <= len(angles) <= 721 or len(levels) != len(angles):
        raise ValueError("matched bounded angle and level arrays required")
    for angle in angles:
        _number(angle, -180.0, 180.0)
    for level in levels:
        _number(level, -120.0, 200.0)
    if any(right <= left for left, right in zip(angles, angles[1:])) or 0 not in angles:
        raise ValueError("strictly increasing polar angles containing zero required")
    if set(angles) != {-angle for angle in angles}:
        raise ValueError("symmetric supplied angle coordinates required for asymmetry review")
    if parameters["angle_alignment_bound_deg"] > parameters["maximum_angle_alignment_bound_deg"]:
        raise ValueError("alignment uncertainty exceeds declared applicability")


def analyze(parameters):
    validate(parameters)
    p = parameters
    angles = p["angles_deg"]
    levels = p["levels_db"]
    by_angle = dict(zip(angles, levels))
    on_axis = by_angle[0]
    coverage = angles[-1] - angles[0]
    maximum_gap = max(right - left for left, right in zip(angles, angles[1:]))
    edge = [on_axis - levels[0], on_axis - levels[-1]]
    edge_lower = [value - 2 * p["level_uncertainty_db"] for value in edge]
    pair_errors = [abs(by_angle[angle] - by_angle[-angle]) for angle in angles if angle < 0]
    maximum_symmetry = max(pair_errors, default=0.0)
    symmetry_upper = maximum_symmetry + 2 * p["level_uncertainty_db"]
    reference_error_upper = abs(on_axis - p["supplied_on_axis_reference_db"]) + p["level_uncertainty_db"]
    checks = [
        {"id": "ANGULAR_COVERAGE", "actual": coverage, "limit": p["minimum_coverage_deg"],
         "passed": coverage >= p["minimum_coverage_deg"], "on_failure": "EXTEND_POLAR_ANGLE_COVERAGE"},
        {"id": "ANGULAR_SAMPLING", "actual": maximum_gap, "limit": p["maximum_angular_gap_deg"],
         "passed": maximum_gap <= p["maximum_angular_gap_deg"], "on_failure": "ADD_ANGLE_SAMPLES_BEFORE_LOBE_DECISION"},
        {"id": "ABSOLUTE_REFERENCE", "actual": reference_error_upper, "limit": p["maximum_on_axis_reference_error_db"],
         "passed": reference_error_upper <= p["maximum_on_axis_reference_error_db"],
         "on_failure": "RESTORE_ABSOLUTE_LEVEL_REFERENCE_BEFORE_NORMALIZED_COMPARISON"},
        {"id": "EDGE_ATTENUATION", "actual": edge_lower, "limit": p["minimum_edge_attenuation_db"],
         "passed": min(edge_lower) >= p["minimum_edge_attenuation_db"],
         "on_failure": "REVIEW_BAFFLE_BOUNDARY_AND_CROSSOVER_BEFORE_DIRECTIVITY_ACCEPTANCE"},
        {"id": "SYMMETRY", "actual": symmetry_upper, "limit": p["maximum_symmetry_error_db"],
         "passed": symmetry_upper <= p["maximum_symmetry_error_db"],
         "on_failure": "RECHECK_ANGLE_ALIGNMENT_FIXTURE_AND_ASYMMETRIC_RADIATION"},
        {"id": "ANGLE_ALIGNMENT", "actual": p["angle_alignment_bound_deg"],
         "limit": p["maximum_angle_alignment_bound_deg"],
         "passed": p["angle_alignment_bound_deg"] <= p["maximum_angle_alignment_bound_deg"],
         "on_failure": "REDUCE_ANGULAR_ALIGNMENT_UNCERTAINTY"},
    ]
    return {
        "coverage_deg": coverage,
        "maximum_gap_deg": maximum_gap,
        "on_axis_level_db": on_axis,
        "on_axis_reference_error_upper_db": reference_error_upper,
        "edge_attenuation_db": edge,
        "edge_attenuation_lower_db": edge_lower,
        "pair_symmetry_errors_db": pair_errors,
        "maximum_symmetry_error_db": maximum_symmetry,
        "symmetry_error_upper_db": symmetry_upper,
        "checks": checks,
        "required_revisions": [row["on_failure"] for row in checks if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "continuous_angle_verified": False,
        "waveguide_cause_verified": False,
        "physical_measurement_verified": False,
        "counter_hypotheses": [
            "Baffle diffraction rather than crossover defect",
            "Angle or acoustic-center alignment error rather than asymmetric radiation",
        ],
        "next_discriminating_experiment": "REPEAT_ABSOLUTE_POLAR_WITH_FINER_ANGLE_GRID_AND_REVERSED_FIXTURE_ORIENTATION",
        "model_assumptions": [
            "Supplied horizontal samples share one absolute level reference",
            "Symmetric coordinates permit pairwise left-right comparison",
            "Scalar level uncertainty is conservatively applied to differences",
            "No interpolation or continuous-angle lobe search is performed",
        ],
        "unresolved": [
            "Unobserved angles, vertical polar and full-sphere directivity",
            "Baffle, crossover, acoustic-center and fixture causal attribution",
            "Calibrated measurement and qualified Human acceptance",
        ],
    }
