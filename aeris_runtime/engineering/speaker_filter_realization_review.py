"""Independent R005 reconstruction of bounded R024 filter assertions."""
from __future__ import annotations

import math


def _same(actual, expected):
    if isinstance(expected, dict): return isinstance(actual, dict) and set(actual)==set(expected) and all(_same(actual[k],v) for k,v in expected.items())
    if isinstance(expected, list): return isinstance(actual,list) and len(actual)==len(expected) and all(_same(a,b) for a,b in zip(actual,expected))
    if isinstance(expected,bool) or expected is None: return actual is expected
    if isinstance(expected,(int,float)): return isinstance(actual,(int,float)) and not isinstance(actual,bool) and math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-12)
    return actual==expected


def review(parameters,candidate):
    from .speaker_filter_realization import validate,_values
    validate(parameters)
    if not isinstance(candidate,dict): raise ValueError("filter-realization candidate object required")
    p=parameters; pole_radii,quantization_error,crossover_sum,crossover_deviation,output_peak=_values(p); max_radius=max(pole_radii)
    raw=[
        ("POLE_STABILITY",max_radius,p["maximum_pole_radius"],"<=","REVISE_BIQUAD_POLES_AND_RECHECK_QUANTIZED_STABILITY"),
        ("COEFFICIENT_QUANTIZATION",quantization_error,p["maximum_coefficient_quantization_error"],"<=","INCREASE_COEFFICIENT_PRECISION_OR_REDESIGN_SECTIONS"),
        ("CROSSOVER_SUM",crossover_deviation,p["maximum_crossover_sum_deviation_db"],"<=","REVISE_CROSSOVER_MAGNITUDE_SUM"),
        ("CROSSOVER_PHASE",abs(p["relative_phase_deg"]),p["maximum_phase_mismatch_deg"],"<=","REVISE_CROSSOVER_PHASE_OR_POLARITY"),
        ("OUTPUT_HEADROOM",output_peak,p["available_output_peak_linear"],"<=","REDUCE_SECTION_GAIN_OR_INPUT_LEVEL"),
        ("GROUP_DELAY",p["group_delay_ms"],p["maximum_group_delay_ms"],"<=","REDUCE_FILTER_ORDER_OR_REVISE_LATENCY_BUDGET")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={
        "pole_radii":pole_radii,"maximum_pole_radius_actual":max_radius,"maximum_coefficient_quantization_error_actual":quantization_error,
        "crossover_sum_linear":crossover_sum,"crossover_sum_deviation_db":crossover_deviation,"estimated_output_peak_linear":output_peak,
        "checks":rows,"required_revisions":[row["on_failure"] for row in rows if not row["passed"]],
        "disposition":"BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in rows) else "DESIGN_REVISION_REQUIRED",
        "realized_frequency_response_verified":False,"fixed_point_runtime_verified":False,"physical_playback_verified":False,"physical_measurement_verified":False,
        "counter_hypotheses":["Polarity or phase mismatch rather than magnitude-EQ error","Coefficient quantization rather than acoustic variation","Upstream clipping rather than unstable filter"],
        "next_discriminating_experiment":"RENDER_QUANTIZED_IMPULSE_RESPONSE_AND_CAPTURE_INTERNAL_PEAKS_AT_WORST_CASE_INPUT",
        "model_assumptions":["Real normalized second-order denominator coefficients","Declared per-section peak gains are conservative scalar bounds","Crossover sum is evaluated only at one declared crossover sample"],
        "unresolved":["Full-band complex response and limit cycles","Runtime coefficient arithmetic, saturation and denormal behavior","Physical playback, calibrated response and qualified Human acceptance"],
    }
    if set(candidate)!=set(expected): raise ValueError("exact filter-realization assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"speaker-filter-realization","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,
            "observations":{"filter_scope":"declared biquads and one crossover sample","unresolved":"full-band fixed-point runtime"},
            "human_approval":False,"role_l3_awarded":False,"scope":"bounded speaker-filter realization report consistency only"}
