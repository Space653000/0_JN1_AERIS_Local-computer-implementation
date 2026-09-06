"""Bounded R049 circumaural seal, ANC margin and output screening."""
from __future__ import annotations
import math

SCALARS={"cushion_leak_pole_hz":(0.0,20000.0),"bass_reference_hz":(1.0,20000.0),"maximum_leak_loss_db":(0.0,60.0),"fit_state_count":(1,10000),"minimum_fit_state_count":(1,10000),"feedback_crossover_hz":(1.0,10000.0),"feedback_delay_ms":(0.0,100.0),"plant_phase_lag_deg":(0.0,180.0),"minimum_phase_margin_deg":(0.0,180.0),"driver_peak_excursion_mm":(0.0,100.0),"safe_peak_excursion_mm":(0.001,100.0),"cushion_compression_fraction":(0.0,1.0),"maximum_cushion_compression_fraction":(0.0,1.0),"earcup_pressure_proxy_pa":(0.0,1000.0),"maximum_earcup_pressure_proxy_pa":(0.0,1000.0)}

def _number(v,lo,hi):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi: raise ValueError("finite declared over-ear value outside bounded applicability")

def validate(p):
    expected=set(SCALARS)|{"model","cushion_interface","physical_fit_verified","full_loop_stability_verified"}
    if not isinstance(p,dict) or set(p)!=expected: raise ValueError("exact supplied over-ear ANC budget required")
    if p["model"]!="SUPPLIED_OVER_EAR_ANC_SEAL_STABILITY": raise ValueError("unsupported over-ear model")
    if p["cushion_interface"] not in {"CIRCUMAURAL_FOAM","CIRCUMAURAL_GEL"}: raise ValueError("unsupported cushion interface")
    if p["physical_fit_verified"] is not False or p["full_loop_stability_verified"] is not False: raise ValueError("physical fit and full-loop stability require external Evidence")
    for k,b in SCALARS.items():_number(p[k],*b)
    for k in ("fit_state_count","minimum_fit_state_count"):
        if not isinstance(p[k],int):raise ValueError("integer fit-state count required")

def _values(p):
    loss=10*math.log10(1+(p["cushion_leak_pole_hz"]/p["bass_reference_hz"])**2)
    margin=180-p["plant_phase_lag_deg"]-0.36*p["feedback_crossover_hz"]*p["feedback_delay_ms"]
    return loss,margin

def analyze(p):
    validate(p);loss,margin=_values(p)
    raw=[("FIT_STATE_COVERAGE",p["fit_state_count"],p["minimum_fit_state_count"],">=","EXPAND_HEAD_SHAPE_GLASSES_AND_CUSHION_FIT_MATRIX"),("CUSHION_LEAK_LOSS",loss,p["maximum_leak_loss_db"],"<=","REVISE_CUSHION_SEAL_BEFORE_BASS_OR_ANC_GAIN"),("FEEDBACK_PHASE_MARGIN",margin,p["minimum_phase_margin_deg"],">=","LOWER_CROSSOVER_OR_LATENCY_AND_REMEASURE_ALL_FIT_LOOPS"),("DRIVER_EXCURSION",p["driver_peak_excursion_mm"],p["safe_peak_excursion_mm"],"<=","LIMIT_BASS_DRIVE_OR_REVISE_DRIVER"),("CUSHION_COMPRESSION",p["cushion_compression_fraction"],p["maximum_cushion_compression_fraction"],"<=","REVISE_CLAMP_CUSHION_OR_FIT_RANGE"),("EARCUP_PRESSURE_PROXY",p["earcup_pressure_proxy_pa"],p["maximum_earcup_pressure_proxy_pa"],"<=","REDUCE_LOW_FREQUENCY_CONTROL_AND_REQUIRE_LISTENER_REVIEW")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"cushion_leak_loss_db":loss,"feedback_phase_margin_deg":margin,"cushion_interface":p["cushion_interface"],"checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED","physical_fit_verified":False,"full_loop_stability_verified":False,"pressure_sensation_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Glasses/cushion leakage rather than insufficient driver bass","Microphone placement rather than ANC algorithm instability","Cushion compression rather than static pressure control"],"next_discriminating_experiment":"MEASURE_MULTI_HEAD_FIT_SEAL_LOOP_TRANSFER_EXCURSION_AND_LISTENER_PRESSURE_RESPONSE","model_assumptions":["Cushion leak uses a supplied single-pole attenuation","ANC margin uses one supplied feedback crossover and delay","Excursion, compression and pressure proxy are supplied scalars"],"unresolved":["Head/cushion population and glasses leakage distribution","Full multi-crossover nonlinear ANC loop and transducer behavior","Calibrated fit, listener pressure sensation and qualified Human approval"]}
