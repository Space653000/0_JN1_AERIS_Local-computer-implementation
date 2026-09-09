"""Bounded R042 echo-control alignment, double-talk and residual screening."""
from __future__ import annotations
import math


SCALARS={"echo_return_before_rms":(1e-12,1e6),"echo_residual_after_rms":(1e-12,1e6),"minimum_erle_db":(0,200),"near_speech_before_rms":(1e-12,1e6),"near_speech_after_rms":(1e-12,1e6),"maximum_near_speech_loss_db":(0,100),"alignment_delay_ms":(0,1e6),"maximum_alignment_delay_ms":(0,1e6),"clock_drift_ppm":(0,1e6),"maximum_clock_drift_ppm":(0,1e6),"double_talk_adaptation_gain":(0,100),"maximum_double_talk_adaptation_gain":(0,100),"adaptive_filter_tail_ms":(0,1e6),"minimum_required_echo_tail_ms":(0,1e6),"nonlinear_residual_rms":(0,1e6),"maximum_nonlinear_residual_rms":(0,1e6)}


def _number(v,low,high):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low<=v<=high:raise ValueError("finite declared AEC value outside bounded applicability")


def validate(p):
    if not isinstance(p,dict) or set(p)!=set(SCALARS)|{"model"}:raise ValueError("exact supplied echo-control contract required")
    if p["model"]!="SUPPLIED_ECHO_CONTROL_METRICS":raise ValueError("unsupported echo-control model")
    for k,b in SCALARS.items():_number(p[k],*b)
    if p["echo_residual_after_rms"]>p["echo_return_before_rms"]:raise ValueError("residual exceeds declared pre-cancellation echo")


def _values(p):
    erle=20*math.log10(p["echo_return_before_rms"]/p["echo_residual_after_rms"])
    near_loss=20*math.log10(p["near_speech_before_rms"]/p["near_speech_after_rms"])
    tail_margin=p["adaptive_filter_tail_ms"]-p["minimum_required_echo_tail_ms"]
    return erle,near_loss,tail_margin


def analyze(parameters):
    validate(parameters);p=parameters;erle,near_loss,tail_margin=_values(p)
    raw=[("ERLE",erle,p["minimum_erle_db"],">=","REVISE_ECHO_MODEL_ALIGNMENT_OR_ADAPTATION"),("NEAR_SPEECH_PRESERVATION",near_loss,p["maximum_near_speech_loss_db"],"<=","FREEZE_ADAPTATION_AND_PRESERVE_NEAR_END_SPEECH"),("ALIGNMENT_DELAY",p["alignment_delay_ms"],p["maximum_alignment_delay_ms"],"<=","REALIGN_PLAYBACK_REFERENCE_AND_CAPTURE_TIMESTAMPS"),("CLOCK_DRIFT",p["clock_drift_ppm"],p["maximum_clock_drift_ppm"],"<=","ENABLE_DRIFT_TRACKING_OR_RESAMPLING"),("DOUBLE_TALK_ADAPTATION",p["double_talk_adaptation_gain"],p["maximum_double_talk_adaptation_gain"],"<=","REDUCE_OR_FREEZE_ADAPTATION_DURING_DOUBLE_TALK"),("ECHO_TAIL_COVERAGE",tail_margin,0.0,">=","INCREASE_ADAPTIVE_FILTER_TAIL_OR_BOUND_ROOM_PATH"),("NONLINEAR_RESIDUAL",p["nonlinear_residual_rms"],p["maximum_nonlinear_residual_rms"],"<=","SEPARATE_PLAYBACK_NONLINEARITY_FROM_LINEAR_ECHO_TAIL")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"erle_db":erle,"near_speech_loss_db":near_loss,"echo_tail_margin_ms":tail_margin,"checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED","speech_quality_verified":False,"echo_path_measured":False,"physical_measurement_verified":False,"counter_hypotheses":["Reference misalignment rather than insufficient adaptive length","Clock drift rather than static echo delay","Nonlinear playback rather than linear-filter weakness"],"next_discriminating_experiment":"REPLAY_SYNCHRONIZED_FAR_END_NEAR_END_DOUBLE_TALK_WITH_DRIFT_AND_NONLINEAR_PLAYBACK_MARKERS","model_assumptions":["Supplied aligned scalar RMS intervals","Near-speech loss is a level proxy, not intelligibility","One declared echo-tail duration and drift bound"],"unresolved":["Time-varying and nonlinear echo path","Corpus-level double-talk speech preservation","Measured acoustic path, perceptual quality and Human acceptance"]}
