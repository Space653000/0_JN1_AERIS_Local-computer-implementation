"""Independent R041 reconstruction of bounded R035 far-field scenarios."""
from __future__ import annotations
import math


def _same(a,e):
    if isinstance(e,dict):return isinstance(a,dict) and set(a)==set(e) and all(_same(a[k],v) for k,v in e.items())
    if isinstance(e,list):return isinstance(a,list) and len(a)==len(e) and all(_same(x,y) for x,y in zip(a,e))
    if isinstance(e,bool) or e is None:return a is e
    if isinstance(e,(int,float)):return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and math.isclose(a,e,rel_tol=1e-10,abs_tol=1e-12)
    return a==e


def review(parameters,candidate):
    from .far_field_scenarios import validate,_values
    validate(parameters)
    if not isinstance(candidate,dict):raise ValueError("far-field candidate object required")
    p=parameters;scenarios=_values(p);worst=min(r["snr_db"] for r in scenarios);max_distance=max(r["distance_m"] for r in scenarios);max_rt60=max(r["rt60_s"] for r in scenarios)
    competing=any(r["noise_kind"]=="COMPETING_SPEECH" and next(x for x in p["scenarios"] if x["id"]==r["id"])["competing_speech_rms_pa"]>0 for r in scenarios);nonstationary=any(r["noise_kind"]=="NONSTATIONARY" for r in scenarios)
    raw=[("SCENARIO_COVERAGE",len(scenarios),p["minimum_scenario_count"],">=","ADD_DISTINCT_FAR_FIELD_SCENARIOS"),("DISTANCE_COVERAGE",max_distance,p["minimum_maximum_distance_m"],">=","ADD_REQUIRED_FAR_FIELD_DISTANCE"),("WORST_CASE_SNR",worst,p["minimum_worst_case_snr_db"],">=","REVISE_CAPTURE_GAIN_APERTURE_OR_NOISE_REQUIREMENT"),("REVERBERATION_COVERAGE",max_rt60,p["maximum_rt60_s"],"<=","REVISE_ROOM_OR_DEREVERBERATION_OPERATING_BOUND"),("COMPETING_SPEECH_COVERAGE",competing,True,"==","ADD_COMPETING_SPEECH_SCENARIO"),("NONSTATIONARY_NOISE_COVERAGE",nonstationary,True,"==","ADD_NONSTATIONARY_NOISE_SCENARIO")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a>=l if o==">=" else a<=l if o=="<=" else a is l,"on_failure":f} for i,a,l,o,f in raw]
    if not p["require_competing_speech"]:checks[4]["passed"]=True
    expected={"scenario_results":scenarios,"worst_case_snr_db":worst,"maximum_distance_m":max_distance,"maximum_rt60_s":max_rt60,"competing_speech_covered":competing,"nonstationary_noise_covered":nonstationary,"checks":checks,
        "required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED","speech_quality_verified":False,"room_measurement_verified":False,"physical_measurement_verified":False,
        "counter_hypotheses":["Room decay rather than noise-reduction weakness","Playback leakage rather than ambient noise","Near-field level extrapolation rather than far-field robustness"],"next_discriminating_experiment":"REPLAY_LEVEL_MATCHED_SPEECH_AT_ALL_DISTANCES_WITH_COMPETING_TALKER_NONSTATIONARY_NOISE_AND_MEASURED_ROOM_IR","model_assumptions":["Free-field inverse-distance speech scaling","Ambient and competing RMS pressures combine uncorrelated","Scalar RT60 does not encode early reflections or spatial variation"],"unresolved":["Speech corpus and talker variability","Measured room impulse responses and self-echo","Perceptual quality, calibrated far-field acceptance and Human review"]}
    if set(candidate)!=set(expected):raise ValueError("exact far-field assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"microphone-far-field-disturbance","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,
        "observations":{"scenario_scope":"supplied scalar distance/noise/RT60 cases","unresolved":"measured room and speech corpus"},"human_approval":False,"role_l3_awarded":False,"scope":"bounded far-field scenario report consistency only"}
