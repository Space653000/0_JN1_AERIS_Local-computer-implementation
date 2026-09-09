"""Independent R038 reconstruction of bounded R036 tonal assertions."""
from __future__ import annotations
import math


def _same(a,e):
    if isinstance(e,dict):return isinstance(a,dict) and set(a)==set(e) and all(_same(a[k],v) for k,v in e.items())
    if isinstance(e,list):return isinstance(a,list) and len(a)==len(e) and all(_same(x,y) for x,y in zip(a,e))
    if isinstance(e,bool) or e is None:return a is e
    if isinstance(e,(int,float)):return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and math.isclose(a,e,rel_tol=1e-10,abs_tol=1e-12)
    return a==e


def review(parameters,candidate):
    from .microphone_tonal import validate,_values
    validate(parameters)
    if not isinstance(candidate,dict):raise ValueError("microphone-tonal candidate object required")
    p=parameters;correction,boost,cut,output_peak,headroom=_values(p)
    raw=[("BOOST_BOUND",boost,p["maximum_boost_db"],"<=","REDUCE_MICROPHONE_EQ_BOOST_OR_REVISE_ACOUSTIC_PATH"),("CUT_BOUND",cut,p["maximum_cut_db"],"<=","REVISE_TARGET_OR_MICROPHONE_RESPONSE"),("OUTPUT_HEADROOM",headroom,p["minimum_output_headroom_db"],">=","REDUCE_EQ_GAIN_OR_UPSTREAM_CAPTURE_LEVEL"),("VOICE_HIGHPASS",p["highpass_corner_hz"],p["maximum_voice_highpass_corner_hz"],"<=","LOWER_HIGHPASS_CORNER_TO_PRESERVE_VOICE_FUNDAMENTALS"),("SMOOTHING_RESOLUTION",p["smoothing_fraction_octave"],p["maximum_smoothing_fraction_octave"],"<=","USE_FINER_SMOOTHING_BEFORE_TONAL_DECISION"),("CAPSULE_OVERLOAD_MARGIN",p["capsule_overload_margin_db"],p["minimum_capsule_overload_margin_db"],">=","REDUCE_ANALOG_GAIN_OR_SELECT_HIGHER_OVERLOAD_CAPSULE")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"proposed_correction_db":correction,"boost_upper_db":boost,"cut_upper_db":cut,"estimated_output_peak_dbfs":output_peak,"output_headroom_lower_db":headroom,"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED","intelligibility_verified":False,"port_transfer_verified":False,"capsule_overload_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Mount cavity rather than capsule coloration","Distance proximity effect rather than EQ defect","Inverse port boost rather than intrinsic tonal deficit"],"next_discriminating_experiment":"CAPTURE_LEVEL_MATCHED_MULTIPLE_DISTANCE_RESPONSE_WITH_PORT_BYPASS_AND_ANALOG_OVERLOAD_MONITORING","model_assumptions":["Pointwise supplied magnitude samples only","Symmetric deterministic response uncertainty","Peak headroom uses worst positive correction without crest redistribution"],"unresolved":["Complex phase and realizable filter response","Fit/distance/port population variation","Speech intelligibility, calibrated overload and Human acceptance"]}
    if set(candidate)!=set(expected):raise ValueError("exact microphone-tonal assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"microphone-tonal-intelligibility","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,"observations":{"tonal_scope":"supplied magnitude/headroom only","unresolved":"speech intelligibility and realized filter"},"human_approval":False,"role_l3_awarded":False,"scope":"bounded microphone tonal report consistency only"}
