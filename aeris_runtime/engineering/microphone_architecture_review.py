"""Independent R039 reconstruction of bounded R027 acoustic-path assertions."""
from __future__ import annotations
import math


def _same(a,e):
    if isinstance(e,dict): return isinstance(a,dict) and set(a)==set(e) and all(_same(a[k],v) for k,v in e.items())
    if isinstance(e,list): return isinstance(a,list) and len(a)==len(e) and all(_same(x,y) for x,y in zip(a,e))
    if isinstance(e,bool) or e is None:return a is e
    if isinstance(e,(int,float)):return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and math.isclose(a,e,rel_tol=1e-10,abs_tol=1e-12)
    return a==e


def review(parameters,candidate):
    from .microphone_architecture import validate,_values
    validate(parameters)
    if not isinstance(candidate,dict):raise ValueError("microphone-architecture candidate object required")
    p=parameters;sensitivity,sensitivity_lower,alias_frequency,overload_margin=_values(p)
    raw=[
        ("SYSTEM_SENSITIVITY",sensitivity_lower,p["minimum_system_sensitivity_dbv_per_pa"],">=","REDUCE_PORT_LOSS_OR_SELECT_HIGHER_SENSITIVITY_CAPSULE"),
        ("SELF_NOISE",p["capsule_self_noise_spl_db"],p["maximum_self_noise_spl_db"],"<=","SELECT_LOWER_NOISE_CAPSULE_OR_REVISE_CAPTURE_RANGE"),
        ("ACOUSTIC_OVERLOAD",overload_margin,0.0,">=","INCREASE_CAPSULE_OVERLOAD_MARGIN_OR_REDUCE_REQUIRED_MAXIMUM_SPL"),
        ("ARRAY_ALIAS_GUARD",alias_frequency,p["maximum_operating_frequency_hz"],">=","REDUCE_ELEMENT_SPACING_OR_LIMIT_ARRAY_BANDWIDTH"),
        ("ARRAY_ELEMENT_COVERAGE",p["array_element_count"],p["minimum_array_element_count"],">=","ADD_ELEMENTS_OR_REVISE_SPATIAL_REQUIREMENT"),
        ("PORT_INSERTION_LOSS",p["port_insertion_loss_db"],p["maximum_port_loss_db"],"<=","REVISE_PORT_MESH_DUCT_OR_SENSITIVITY_BUDGET")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"system_sensitivity_dbv_per_pa":sensitivity,"system_sensitivity_lower_dbv_per_pa":sensitivity_lower,
        "spatial_alias_frequency_hz":alias_frequency,"acoustic_overload_margin_db":overload_margin,"port_path_kind":p["port_path_kind"],
        "array_geometry_kind":p["array_geometry_kind"],"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],
        "disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED",
        "capsule_characterization_verified":False,"port_transfer_verified":False,"array_performance_verified":False,"physical_measurement_verified":False,
        "counter_hypotheses":["Mesh insertion loss rather than capsule sensitivity shift","Frontend noise rather than capsule self-noise","Array spacing rather than noise-reduction weakness"],
        "next_discriminating_experiment":"MEASURE_CAPSULE_PORT_TRANSFER_NOISE_OVERLOAD_AND_ARRAY_RESPONSE_IN_ONE_REFERENCED_FIXTURE",
        "model_assumptions":["Port loss is a supplied scalar at the decision band","Far-field alias guard uses half-wavelength spacing","Capsule tolerance is a deterministic symmetric dB bound"],
        "unresolved":["Frequency-dependent port and mesh transfer","Capsule production distribution and frontend noise","Measured array manifold, overload and qualified Human acceptance"]}
    if set(candidate)!=set(expected):raise ValueError("exact microphone-architecture assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"microphone-architecture-acoustic-path","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,
        "observations":{"architecture_scope":"declared capsule/port/array scalars","unresolved":"frequency-dependent physical acoustic path"},
        "human_approval":False,"role_l3_awarded":False,"scope":"bounded microphone architecture report consistency only"}
