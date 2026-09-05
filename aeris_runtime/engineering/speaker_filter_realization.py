"""Bounded R024 biquad/crossover realization screening."""
from __future__ import annotations

import cmath
import math


SCALARS = {
    "coefficient_fractional_bits": (4, 52), "maximum_pole_radius": (0.0, 0.999999999999),
    "maximum_coefficient_quantization_error": (0.0, 1.0),
    "lowpass_gain_at_crossover": (0.0, 1000.0), "highpass_gain_at_crossover": (0.0, 1000.0),
    "relative_phase_deg": (-360.0, 360.0), "maximum_phase_mismatch_deg": (0.0, 180.0),
    "maximum_crossover_sum_deviation_db": (0.0, 100.0), "input_peak_linear": (0.0, 1000.0),
    "available_output_peak_linear": (0.0, 1000.0), "group_delay_ms": (0.0, 1e6),
    "maximum_group_delay_ms": (0.0, 1e6),
}


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite declared filter value outside bounded applicability")


def validate(parameters):
    expected = set(SCALARS) | {"model", "sections", "section_peak_gains"}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact supplied speaker filter realization contract required")
    if parameters["model"] != "SUPPLIED_SPEAKER_BIQUAD_CROSSOVER": raise ValueError("unsupported filter model")
    for key, bounds in SCALARS.items(): _number(parameters[key], *bounds)
    if not isinstance(parameters["coefficient_fractional_bits"], int): raise ValueError("integer fractional-bit count required")
    sections = parameters["sections"]; peaks = parameters["section_peak_gains"]
    if not isinstance(sections, list) or not 1 <= len(sections) <= 32 or not isinstance(peaks, list) or len(peaks) != len(sections):
        raise ValueError("aligned bounded biquad sections and peak gains required")
    for section in sections:
        if not isinstance(section, dict) or set(section) != {"b", "a"} or len(section["b"]) != 3 or len(section["a"]) != 3:
            raise ValueError("exact second-order coefficient vectors required")
        for value in section["b"] + section["a"]: _number(value, -1e6, 1e6)
        if section["a"][0] != 1.0: raise ValueError("normalized a0=1 coefficient required")
    for peak in peaks: _number(peak, 0.0, 1e6)


def _values(parameters):
    p = parameters; scale = 2 ** p["coefficient_fractional_bits"]
    pole_radii=[]; maximum_quantization_error=0.0
    for section in p["sections"]:
        a1, a2 = section["a"][1:]
        discriminant = complex(a1*a1 - 4*a2)
        roots = ((-a1 + cmath.sqrt(discriminant))/2, (-a1 - cmath.sqrt(discriminant))/2)
        pole_radii.extend(abs(root) for root in roots)
        for value in section["b"] + section["a"]:
            maximum_quantization_error=max(maximum_quantization_error, abs(round(value*scale)/scale-value))
    phase=math.radians(p["relative_phase_deg"])
    crossover_sum=abs(p["lowpass_gain_at_crossover"] + p["highpass_gain_at_crossover"]*complex(math.cos(phase),math.sin(phase)))
    crossover_deviation=abs(20*math.log10(crossover_sum)) if crossover_sum > 0 else math.inf
    output_peak=p["input_peak_linear"]*math.prod(p["section_peak_gains"])
    return pole_radii, maximum_quantization_error, crossover_sum, crossover_deviation, output_peak


def analyze(parameters):
    validate(parameters); p=parameters
    pole_radii, quantization_error, crossover_sum, crossover_deviation, output_peak = _values(p)
    max_radius=max(pole_radii)
    raw=[
        ("POLE_STABILITY", max_radius, p["maximum_pole_radius"], "<=", "REVISE_BIQUAD_POLES_AND_RECHECK_QUANTIZED_STABILITY"),
        ("COEFFICIENT_QUANTIZATION", quantization_error, p["maximum_coefficient_quantization_error"], "<=", "INCREASE_COEFFICIENT_PRECISION_OR_REDESIGN_SECTIONS"),
        ("CROSSOVER_SUM", crossover_deviation, p["maximum_crossover_sum_deviation_db"], "<=", "REVISE_CROSSOVER_MAGNITUDE_SUM"),
        ("CROSSOVER_PHASE", abs(p["relative_phase_deg"]), p["maximum_phase_mismatch_deg"], "<=", "REVISE_CROSSOVER_PHASE_OR_POLARITY"),
        ("OUTPUT_HEADROOM", output_peak, p["available_output_peak_linear"], "<=", "REDUCE_SECTION_GAIN_OR_INPUT_LEVEL"),
        ("GROUP_DELAY", p["group_delay_ms"], p["maximum_group_delay_ms"], "<=", "REDUCE_FILTER_ORDER_OR_REVISE_LATENCY_BUDGET"),
    ]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l,"on_failure":f} for i,a,l,o,f in raw]
    return {
        "pole_radii":pole_radii,"maximum_pole_radius_actual":max_radius,"maximum_coefficient_quantization_error_actual":quantization_error,
        "crossover_sum_linear":crossover_sum,"crossover_sum_deviation_db":crossover_deviation,"estimated_output_peak_linear":output_peak,
        "checks":checks,"required_revisions":[row["on_failure"] for row in checks if not row["passed"]],
        "disposition":"BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
        "realized_frequency_response_verified":False,"fixed_point_runtime_verified":False,"physical_playback_verified":False,"physical_measurement_verified":False,
        "counter_hypotheses":["Polarity or phase mismatch rather than magnitude-EQ error","Coefficient quantization rather than acoustic variation","Upstream clipping rather than unstable filter"],
        "next_discriminating_experiment":"RENDER_QUANTIZED_IMPULSE_RESPONSE_AND_CAPTURE_INTERNAL_PEAKS_AT_WORST_CASE_INPUT",
        "model_assumptions":["Real normalized second-order denominator coefficients","Declared per-section peak gains are conservative scalar bounds","Crossover sum is evaluated only at one declared crossover sample"],
        "unresolved":["Full-band complex response and limit cycles","Runtime coefficient arithmetic, saturation and denormal behavior","Physical playback, calibrated response and qualified Human acceptance"],
    }
