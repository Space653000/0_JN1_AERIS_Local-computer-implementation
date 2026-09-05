"""Bounded R036 microphone tonal-response and headroom screening."""
from __future__ import annotations
import math


def _number(v,low,high):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low<=v<=high:raise ValueError("finite declared microphone tonal value outside bounded applicability")


def validate(p):
    arrays={"frequency_hz","response_db","target_db"};scalars={"response_uncertainty_db":(0,100),"maximum_boost_db":(0,100),"maximum_cut_db":(0,100),"input_peak_dbfs":(-300,0),"minimum_output_headroom_db":(0,100),"highpass_corner_hz":(1,1e6),"maximum_voice_highpass_corner_hz":(1,1e6),"smoothing_fraction_octave":(1/96,8),"maximum_smoothing_fraction_octave":(1/96,8),"capsule_overload_margin_db":(-100,200),"minimum_capsule_overload_margin_db":(0,200)}
    if not isinstance(p,dict) or set(p)!=arrays|set(scalars)|{"model"}:raise ValueError("exact supplied microphone tonal contract required")
    if p["model"]!="SUPPLIED_MICROPHONE_TONAL_RESPONSE":raise ValueError("unsupported microphone tonal model")
    for k,b in scalars.items():_number(p[k],*b)
    if p["input_peak_dbfs"]>0:raise ValueError("input peak must use dBFS at or below full scale")
    n=len(p["frequency_hz"])
    if n<3 or n>4096 or len(p["response_db"])!=n or len(p["target_db"])!=n:raise ValueError("aligned bounded tonal samples required")
    for key in arrays:
        if not isinstance(p[key],list):raise ValueError("tonal vectors required")
        for v in p[key]:_number(v,1e-9 if key=="frequency_hz" else -300,1e7 if key=="frequency_hz" else 300)
    if any(b<=a for a,b in zip(p["frequency_hz"],p["frequency_hz"][1:])):raise ValueError("strictly increasing frequency samples required")


def _values(p):
    correction=[t-r for t,r in zip(p["target_db"],p["response_db"])]
    boost=max(correction)+p["response_uncertainty_db"];cut=max(-x for x in correction)+p["response_uncertainty_db"]
    output_peak=p["input_peak_dbfs"]+boost;headroom=-output_peak
    return correction,boost,cut,output_peak,headroom


def analyze(parameters):
    validate(parameters);p=parameters;correction,boost,cut,output_peak,headroom=_values(p)
    raw=[("BOOST_BOUND",boost,p["maximum_boost_db"],"<=","REDUCE_MICROPHONE_EQ_BOOST_OR_REVISE_ACOUSTIC_PATH"),("CUT_BOUND",cut,p["maximum_cut_db"],"<=","REVISE_TARGET_OR_MICROPHONE_RESPONSE"),("OUTPUT_HEADROOM",headroom,p["minimum_output_headroom_db"],">=","REDUCE_EQ_GAIN_OR_UPSTREAM_CAPTURE_LEVEL"),("VOICE_HIGHPASS",p["highpass_corner_hz"],p["maximum_voice_highpass_corner_hz"],"<=","LOWER_HIGHPASS_CORNER_TO_PRESERVE_VOICE_FUNDAMENTALS"),("SMOOTHING_RESOLUTION",p["smoothing_fraction_octave"],p["maximum_smoothing_fraction_octave"],"<=","USE_FINER_SMOOTHING_BEFORE_TONAL_DECISION"),("CAPSULE_OVERLOAD_MARGIN",p["capsule_overload_margin_db"],p["minimum_capsule_overload_margin_db"],">=","REDUCE_ANALOG_GAIN_OR_SELECT_HIGHER_OVERLOAD_CAPSULE")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"proposed_correction_db":correction,"boost_upper_db":boost,"cut_upper_db":cut,"estimated_output_peak_dbfs":output_peak,"output_headroom_lower_db":headroom,"checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED","intelligibility_verified":False,"port_transfer_verified":False,"capsule_overload_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Mount cavity rather than capsule coloration","Distance proximity effect rather than EQ defect","Inverse port boost rather than intrinsic tonal deficit"],"next_discriminating_experiment":"CAPTURE_LEVEL_MATCHED_MULTIPLE_DISTANCE_RESPONSE_WITH_PORT_BYPASS_AND_ANALOG_OVERLOAD_MONITORING","model_assumptions":["Pointwise supplied magnitude samples only","Symmetric deterministic response uncertainty","Peak headroom uses worst positive correction without crest redistribution"],"unresolved":["Complex phase and realizable filter response","Fit/distance/port population variation","Speech intelligibility, calibrated overload and Human acceptance"]}
