"""Independent R044 reconstruction of bounded R042 echo-control assertions."""
from __future__ import annotations
import math


def _same(a,e):
    if isinstance(e,dict):return isinstance(a,dict) and set(a)==set(e) and all(_same(a[k],v) for k,v in e.items())
    if isinstance(e,list):return isinstance(a,list) and len(a)==len(e) and all(_same(x,y) for x,y in zip(a,e))
    if isinstance(e,bool) or e is None:return a is e
    if isinstance(e,(int,float)):return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and math.isclose(a,e,rel_tol=1e-10,abs_tol=1e-12)
    return a==e


def review(parameters,candidate):
    from .aec_control import validate,_values
    validate(parameters)
    if not isinstance(candidate,dict):raise ValueError("AEC candidate object required")
    p=parameters;erle,near_loss,tail_margin=_values(p)
    raw=[("ERLE",erle,p["minimum_erle_db"],">=","REVISE_ECHO_MODEL_ALIGNMENT_OR_ADAPTATION"),("NEAR_SPEECH_PRESERVATION",near_loss,p["maximum_near_speech_loss_db"],"<=","FREEZE_ADAPTATION_AND_PRESERVE_NEAR_END_SPEECH"),("ALIGNMENT_DELAY",p["alignment_delay_ms"],p["maximum_alignment_delay_ms"],"<=","REALIGN_PLAYBACK_REFERENCE_AND_CAPTURE_TIMESTAMPS"),("CLOCK_DRIFT",p["clock_drift_ppm"],p["maximum_clock_drift_ppm"],"<=","ENABLE_DRIFT_TRACKING_OR_RESAMPLING"),("DOUBLE_TALK_ADAPTATION",p["double_talk_adaptation_gain"],p["maximum_double_talk_adaptation_gain"],"<=","REDUCE_OR_FREEZE_ADAPTATION_DURING_DOUBLE_TALK"),("ECHO_TAIL_COVERAGE",tail_margin,0.0,">=","INCREASE_ADAPTIVE_FILTER_TAIL_OR_BOUND_ROOM_PATH"),("NONLINEAR_RESIDUAL",p["nonlinear_residual_rms"],p["maximum_nonlinear_residual_rms"],"<=","SEPARATE_PLAYBACK_NONLINEARITY_FROM_LINEAR_ECHO_TAIL")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"erle_db":erle,"near_speech_loss_db":near_loss,"echo_tail_margin_ms":tail_margin,"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED","speech_quality_verified":False,"echo_path_measured":False,"physical_measurement_verified":False,"counter_hypotheses":["Reference misalignment rather than insufficient adaptive length","Clock drift rather than static echo delay","Nonlinear playback rather than linear-filter weakness"],"next_discriminating_experiment":"REPLAY_SYNCHRONIZED_FAR_END_NEAR_END_DOUBLE_TALK_WITH_DRIFT_AND_NONLINEAR_PLAYBACK_MARKERS","model_assumptions":["Supplied aligned scalar RMS intervals","Near-speech loss is a level proxy, not intelligibility","One declared echo-tail duration and drift bound"],"unresolved":["Time-varying and nonlinear echo path","Corpus-level double-talk speech preservation","Measured acoustic path, perceptual quality and Human acceptance"]}
    if set(candidate)!=set(expected):raise ValueError("exact echo-control assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"microphone-aec-enhancement","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,"observations":{"aec_scope":"supplied scalar alignment/double-talk metrics","unresolved":"time-varying acoustic echo and speech quality"},"human_approval":False,"role_l3_awarded":False,"scope":"bounded echo-control report consistency only"}
