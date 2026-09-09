"""Bounded R027 microphone capsule, port and array architecture screening."""
from __future__ import annotations

import math


SCALARS={
    "capsule_sensitivity_dbv_per_pa":(-200.0,100.0),"port_insertion_loss_db":(0.0,100.0),
    "minimum_system_sensitivity_dbv_per_pa":(-200.0,100.0),"capsule_self_noise_spl_db":(-50.0,200.0),
    "maximum_self_noise_spl_db":(-50.0,200.0),"capsule_acoustic_overload_spl_db":(0.0,250.0),
    "required_acoustic_overload_spl_db":(0.0,250.0),"array_element_count":(1,1024),
    "minimum_array_element_count":(1,1024),"array_spacing_m":(1e-6,100.0),
    "maximum_operating_frequency_hz":(1.0,1e7),"sound_speed_m_s":(100.0,1000.0),
    "maximum_port_loss_db":(0.0,100.0),"sensitivity_tolerance_db":(0.0,100.0),
}


def _number(value,low,high):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError("finite declared microphone architecture value outside bounded applicability")


def validate(parameters):
    expected=set(SCALARS)|{"model","port_path_kind","array_geometry_kind"}
    if not isinstance(parameters,dict) or set(parameters)!=expected: raise ValueError("exact supplied microphone architecture contract required")
    if parameters["model"]!="SUPPLIED_MICROPHONE_ARCHITECTURE": raise ValueError("unsupported microphone architecture model")
    if parameters["port_path_kind"] not in {"DIRECT_PORT","MESHED_PORT","DUCTED_PORT"}: raise ValueError("unsupported port-path class")
    if parameters["array_geometry_kind"] not in {"LINEAR","PLANAR","SINGLE_CAPSULE"}: raise ValueError("unsupported array geometry class")
    for key,bounds in SCALARS.items(): _number(parameters[key],*bounds)
    for key in ("array_element_count","minimum_array_element_count"):
        if not isinstance(parameters[key],int): raise ValueError("integer element-count contract required")
    if parameters["array_geometry_kind"]=="SINGLE_CAPSULE" and parameters["array_element_count"]!=1:
        raise ValueError("single-capsule geometry must contain exactly one element")


def _values(p):
    sensitivity=p["capsule_sensitivity_dbv_per_pa"]-p["port_insertion_loss_db"]
    sensitivity_lower=sensitivity-p["sensitivity_tolerance_db"]
    alias_frequency=p["sound_speed_m_s"]/(2*p["array_spacing_m"])
    overload_margin=p["capsule_acoustic_overload_spl_db"]-p["required_acoustic_overload_spl_db"]
    return sensitivity,sensitivity_lower,alias_frequency,overload_margin


def analyze(parameters):
    validate(parameters);p=parameters
    sensitivity,sensitivity_lower,alias_frequency,overload_margin=_values(p)
    raw=[
        ("SYSTEM_SENSITIVITY",sensitivity_lower,p["minimum_system_sensitivity_dbv_per_pa"],">=","REDUCE_PORT_LOSS_OR_SELECT_HIGHER_SENSITIVITY_CAPSULE"),
        ("SELF_NOISE",p["capsule_self_noise_spl_db"],p["maximum_self_noise_spl_db"],"<=","SELECT_LOWER_NOISE_CAPSULE_OR_REVISE_CAPTURE_RANGE"),
        ("ACOUSTIC_OVERLOAD",overload_margin,0.0,">=","INCREASE_CAPSULE_OVERLOAD_MARGIN_OR_REDUCE_REQUIRED_MAXIMUM_SPL"),
        ("ARRAY_ALIAS_GUARD",alias_frequency,p["maximum_operating_frequency_hz"],">=","REDUCE_ELEMENT_SPACING_OR_LIMIT_ARRAY_BANDWIDTH"),
        ("ARRAY_ELEMENT_COVERAGE",p["array_element_count"],p["minimum_array_element_count"],">=","ADD_ELEMENTS_OR_REVISE_SPATIAL_REQUIREMENT"),
        ("PORT_INSERTION_LOSS",p["port_insertion_loss_db"],p["maximum_port_loss_db"],"<=","REVISE_PORT_MESH_DUCT_OR_SENSITIVITY_BUDGET"),
    ]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"system_sensitivity_dbv_per_pa":sensitivity,"system_sensitivity_lower_dbv_per_pa":sensitivity_lower,
            "spatial_alias_frequency_hz":alias_frequency,"acoustic_overload_margin_db":overload_margin,
            "port_path_kind":p["port_path_kind"],"array_geometry_kind":p["array_geometry_kind"],"checks":checks,
            "required_revisions":[row["on_failure"] for row in checks if not row["passed"]],
            "disposition":"BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
            "capsule_characterization_verified":False,"port_transfer_verified":False,"array_performance_verified":False,"physical_measurement_verified":False,
            "counter_hypotheses":["Mesh insertion loss rather than capsule sensitivity shift","Frontend noise rather than capsule self-noise","Array spacing rather than noise-reduction weakness"],
            "next_discriminating_experiment":"MEASURE_CAPSULE_PORT_TRANSFER_NOISE_OVERLOAD_AND_ARRAY_RESPONSE_IN_ONE_REFERENCED_FIXTURE",
            "model_assumptions":["Port loss is a supplied scalar at the decision band","Far-field alias guard uses half-wavelength spacing","Capsule tolerance is a deterministic symmetric dB bound"],
            "unresolved":["Frequency-dependent port and mesh transfer","Capsule production distribution and frontend noise","Measured array manifold, overload and qualified Human acceptance"]}
