"""Independent reconstruction of supplied speaker polar decision assertions."""
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
    from .speaker_polar import validate

    validate(parameters)
    if not isinstance(candidate, dict):
        raise ValueError("speaker polar candidate object required")
    p = parameters
    samples = sorted(zip(p["angles_deg"], p["levels_db"]), key=lambda item: item[0])
    coordinates = [item[0] for item in samples]
    levels = {angle: level for angle, level in samples}
    on_axis = levels[0]
    coverage = coordinates[-1] - coordinates[0]
    gaps = [coordinates[index + 1] - coordinates[index] for index in range(len(coordinates) - 1)]
    edge = [on_axis - levels[coordinates[0]], on_axis - levels[coordinates[-1]]]
    edge_lower = [value - p["level_uncertainty_db"] - p["level_uncertainty_db"] for value in edge]
    pairs = [abs(levels[left] - levels[-left]) for left in coordinates if left < 0]
    asymmetry = max(pairs, default=0.0)
    asymmetry_upper = asymmetry + p["level_uncertainty_db"] + p["level_uncertainty_db"]
    reference_upper = abs(on_axis - p["supplied_on_axis_reference_db"]) + p["level_uncertainty_db"]
    maximum_gap = max(gaps)
    rows = [
        {"id": "ANGULAR_COVERAGE", "actual": coverage, "limit": p["minimum_coverage_deg"], "passed": coverage >= p["minimum_coverage_deg"], "on_failure": "EXTEND_POLAR_ANGLE_COVERAGE"},
        {"id": "ANGULAR_SAMPLING", "actual": maximum_gap, "limit": p["maximum_angular_gap_deg"], "passed": maximum_gap <= p["maximum_angular_gap_deg"], "on_failure": "ADD_ANGLE_SAMPLES_BEFORE_LOBE_DECISION"},
        {"id": "ABSOLUTE_REFERENCE", "actual": reference_upper, "limit": p["maximum_on_axis_reference_error_db"], "passed": reference_upper <= p["maximum_on_axis_reference_error_db"], "on_failure": "RESTORE_ABSOLUTE_LEVEL_REFERENCE_BEFORE_NORMALIZED_COMPARISON"},
        {"id": "EDGE_ATTENUATION", "actual": edge_lower, "limit": p["minimum_edge_attenuation_db"], "passed": min(edge_lower) >= p["minimum_edge_attenuation_db"], "on_failure": "REVIEW_BAFFLE_BOUNDARY_AND_CROSSOVER_BEFORE_DIRECTIVITY_ACCEPTANCE"},
        {"id": "SYMMETRY", "actual": asymmetry_upper, "limit": p["maximum_symmetry_error_db"], "passed": asymmetry_upper <= p["maximum_symmetry_error_db"], "on_failure": "RECHECK_ANGLE_ALIGNMENT_FIXTURE_AND_ASYMMETRIC_RADIATION"},
        {"id": "ANGLE_ALIGNMENT", "actual": p["angle_alignment_bound_deg"], "limit": p["maximum_angle_alignment_bound_deg"], "passed": p["angle_alignment_bound_deg"] <= p["maximum_angle_alignment_bound_deg"], "on_failure": "REDUCE_ANGULAR_ALIGNMENT_UNCERTAINTY"},
    ]
    expected = {
        "coverage_deg": coverage, "maximum_gap_deg": maximum_gap, "on_axis_level_db": on_axis,
        "on_axis_reference_error_upper_db": reference_upper, "edge_attenuation_db": edge,
        "edge_attenuation_lower_db": edge_lower, "pair_symmetry_errors_db": pairs,
        "maximum_symmetry_error_db": asymmetry, "symmetry_error_upper_db": asymmetry_upper,
        "checks": rows, "required_revisions": [row["on_failure"] for row in rows if not row["passed"]],
        "disposition": "BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "continuous_angle_verified": False, "waveguide_cause_verified": False, "physical_measurement_verified": False,
        "counter_hypotheses": ["Baffle diffraction rather than crossover defect", "Angle or acoustic-center alignment error rather than asymmetric radiation"],
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
    if set(candidate) != set(expected):
        raise ValueError("exact speaker polar assertions required")
    differences = [{"field": key, "asserted": candidate[key], "expected": value} for key, value in expected.items() if not _same(candidate[key], value)]
    return {
        "domain": "speaker-polar-spatial",
        "decision": "CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT",
        "disagreements": differences,
        "observations": {"sampling_scope": "supplied discrete horizontal samples only", "unresolved": "Unobserved angles and physical causal attribution"},
        "human_approval": False, "role_l3_awarded": False,
        "scope": "bounded absolute polar sampling and report consistency only",
    }
