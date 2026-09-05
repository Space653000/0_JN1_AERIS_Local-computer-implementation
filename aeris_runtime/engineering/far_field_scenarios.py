"""Bounded R035 far-field noise, distance and reverberation scenario screen."""
from __future__ import annotations
import math


def _number(v,low,high):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low<=v<=high:raise ValueError("finite declared far-field value outside bounded applicability")


def validate(p):
    expected={"model","scenarios","minimum_scenario_count","minimum_maximum_distance_m","minimum_worst_case_snr_db","maximum_rt60_s","require_competing_speech"}
    if not isinstance(p,dict) or set(p)!=expected:raise ValueError("exact supplied far-field scenario contract required")
    if p["model"]!="SUPPLIED_FAR_FIELD_SCENARIOS":raise ValueError("unsupported far-field scenario model")
    if not isinstance(p["minimum_scenario_count"],int) or not 1<=p["minimum_scenario_count"]<=100:raise ValueError("bounded integer scenario coverage required")
    for key,bounds in (("minimum_maximum_distance_m",(0.0,1000.0)),("minimum_worst_case_snr_db",(-100.0,200.0)),("maximum_rt60_s",(0.0,100.0))):_number(p[key],*bounds)
    if not isinstance(p["require_competing_speech"],bool):raise ValueError("explicit competing-speech policy required")
    rows=p["scenarios"]
    if not isinstance(rows,list) or not 1<=len(rows)<=100:raise ValueError("bounded scenario list required")
    ids=[]
    for row in rows:
        fields={"id","distance_m","reference_distance_m","speech_reference_rms_pa","ambient_noise_rms_pa","competing_speech_rms_pa","rt60_s","noise_kind"}
        if not isinstance(row,dict) or set(row)!=fields:raise ValueError("exact far-field scenario fields required")
        if not isinstance(row["id"],str) or not row["id"].strip() or row["noise_kind"] not in {"STATIONARY","NONSTATIONARY","COMPETING_SPEECH"}:raise ValueError("canonical scenario identity and noise kind required")
        ids.append(row["id"])
        for key in fields-{"id","noise_kind"}:_number(row[key],1e-12 if "rms" in key or "distance" in key else 0.0,1000.0)
    if len(set(ids))!=len(ids):raise ValueError("scenario IDs must be unique")


def _values(p):
    results=[]
    for row in p["scenarios"]:
        speech=row["speech_reference_rms_pa"]*row["reference_distance_m"]/row["distance_m"]
        disturbance=math.hypot(row["ambient_noise_rms_pa"],row["competing_speech_rms_pa"])
        snr=20*math.log10(speech/disturbance)
        results.append({"id":row["id"],"distance_m":row["distance_m"],"speech_rms_pa":speech,"disturbance_rms_pa":disturbance,"snr_db":snr,"rt60_s":row["rt60_s"],"noise_kind":row["noise_kind"]})
    return results


def analyze(parameters):
    validate(parameters);p=parameters;scenarios=_values(p)
    worst=min(r["snr_db"] for r in scenarios);max_distance=max(r["distance_m"] for r in scenarios);max_rt60=max(r["rt60_s"] for r in scenarios)
    competing=any(r["noise_kind"]=="COMPETING_SPEECH" and next(x for x in p["scenarios"] if x["id"]==r["id"])["competing_speech_rms_pa"]>0 for r in scenarios)
    nonstationary=any(r["noise_kind"]=="NONSTATIONARY" for r in scenarios)
    raw=[("SCENARIO_COVERAGE",len(scenarios),p["minimum_scenario_count"],">=","ADD_DISTINCT_FAR_FIELD_SCENARIOS"),
         ("DISTANCE_COVERAGE",max_distance,p["minimum_maximum_distance_m"],">=","ADD_REQUIRED_FAR_FIELD_DISTANCE"),
         ("WORST_CASE_SNR",worst,p["minimum_worst_case_snr_db"],">=","REVISE_CAPTURE_GAIN_APERTURE_OR_NOISE_REQUIREMENT"),
         ("REVERBERATION_COVERAGE",max_rt60,p["maximum_rt60_s"],"<=","REVISE_ROOM_OR_DEREVERBERATION_OPERATING_BOUND"),
         ("COMPETING_SPEECH_COVERAGE",competing,True,"==","ADD_COMPETING_SPEECH_SCENARIO"),
         ("NONSTATIONARY_NOISE_COVERAGE",nonstationary,True,"==","ADD_NONSTATIONARY_NOISE_SCENARIO")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a>=l if o==">=" else a<=l if o=="<=" else a is l,"on_failure":f} for i,a,l,o,f in raw]
    if not p["require_competing_speech"]:checks[4]["passed"]=True
    return {"scenario_results":scenarios,"worst_case_snr_db":worst,"maximum_distance_m":max_distance,"maximum_rt60_s":max_rt60,
        "competing_speech_covered":competing,"nonstationary_noise_covered":nonstationary,"checks":checks,
        "required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED",
        "speech_quality_verified":False,"room_measurement_verified":False,"physical_measurement_verified":False,
        "counter_hypotheses":["Room decay rather than noise-reduction weakness","Playback leakage rather than ambient noise","Near-field level extrapolation rather than far-field robustness"],
        "next_discriminating_experiment":"REPLAY_LEVEL_MATCHED_SPEECH_AT_ALL_DISTANCES_WITH_COMPETING_TALKER_NONSTATIONARY_NOISE_AND_MEASURED_ROOM_IR",
        "model_assumptions":["Free-field inverse-distance speech scaling","Ambient and competing RMS pressures combine uncorrelated","Scalar RT60 does not encode early reflections or spatial variation"],
        "unresolved":["Speech corpus and talker variability","Measured room impulse responses and self-echo","Perceptual quality, calibrated far-field acceptance and Human review"]}
