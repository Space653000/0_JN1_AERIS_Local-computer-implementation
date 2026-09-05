"""Independent R005 reconstruction of the bounded R049 over-ear budget."""
from __future__ import annotations
import math

def _same(a,e):
    if isinstance(e,dict):return isinstance(a,dict) and set(a)==set(e) and all(_same(a[k],v) for k,v in e.items())
    if isinstance(e,list):return isinstance(a,list) and len(a)==len(e) and all(_same(x,y) for x,y in zip(a,e))
    if isinstance(e,bool) or e is None:return a is e
    if isinstance(e,(int,float)):return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and math.isclose(a,e,rel_tol=1e-10,abs_tol=1e-12)
    return a==e

def review(p,candidate):
    from .overear_anc_product import validate,_values
    validate(p)
    if not isinstance(candidate,dict):raise ValueError("over-ear ANC candidate object required")
    loss,margin=_values(p)
    raw=[("FIT_STATE_COVERAGE",p["fit_state_count"],p["minimum_fit_state_count"],">=","EXPAND_HEAD_SHAPE_GLASSES_AND_CUSHION_FIT_MATRIX"),("CUSHION_LEAK_LOSS",loss,p["maximum_leak_loss_db"],"<=","REVISE_CUSHION_SEAL_BEFORE_BASS_OR_ANC_GAIN"),("FEEDBACK_PHASE_MARGIN",margin,p["minimum_phase_margin_deg"],">=","LOWER_CROSSOVER_OR_LATENCY_AND_REMEASURE_ALL_FIT_LOOPS"),("DRIVER_EXCURSION",p["driver_peak_excursion_mm"],p["safe_peak_excursion_mm"],"<=","LIMIT_BASS_DRIVE_OR_REVISE_DRIVER"),("CUSHION_COMPRESSION",p["cushion_compression_fraction"],p["maximum_cushion_compression_fraction"],"<=","REVISE_CLAMP_CUSHION_OR_FIT_RANGE"),("EARCUP_PRESSURE_PROXY",p["earcup_pressure_proxy_pa"],p["maximum_earcup_pressure_proxy_pa"],"<=","REDUCE_LOW_FREQUENCY_CONTROL_AND_REQUIRE_LISTENER_REVIEW")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"cushion_leak_loss_db":loss,"feedback_phase_margin_deg":margin,"cushion_interface":p["cushion_interface"],"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED","physical_fit_verified":False,"full_loop_stability_verified":False,"pressure_sensation_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Glasses/cushion leakage rather than insufficient driver bass","Microphone placement rather than ANC algorithm instability","Cushion compression rather than static pressure control"],"next_discriminating_experiment":"MEASURE_MULTI_HEAD_FIT_SEAL_LOOP_TRANSFER_EXCURSION_AND_LISTENER_PRESSURE_RESPONSE","model_assumptions":["Cushion leak uses a supplied single-pole attenuation","ANC margin uses one supplied feedback crossover and delay","Excursion, compression and pressure proxy are supplied scalars"],"unresolved":["Head/cushion population and glasses leakage distribution","Full multi-crossover nonlinear ANC loop and transducer behavior","Calibrated fit, listener pressure sensation and qualified Human approval"]}
    if set(candidate)!=set(expected):raise ValueError("exact over-ear ANC assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"over-ear-anc-seal-stability","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,"observations":{"bounded_scope":"fit/seal/feedback/excursion/compression/pressure-proxy arithmetic","unresolved":"population fit, full loop and listener response"},"human_approval":False,"role_l3_awarded":False,"scope":"bounded over-ear ANC report consistency only"}
