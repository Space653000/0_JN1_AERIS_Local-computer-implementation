"""Independent R081 reconstruction of the bounded R047 Auracast budget."""
from __future__ import annotations
import math


def _same(a,e):
    if isinstance(e,dict): return isinstance(a,dict) and set(a)==set(e) and all(_same(a[k],v) for k,v in e.items())
    if isinstance(e,list): return isinstance(a,list) and len(a)==len(e) and all(_same(x,y) for x,y in zip(a,e))
    if isinstance(e,bool) or e is None: return a is e
    if isinstance(e,(int,float)): return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and math.isclose(a,e,rel_tol=1e-10,abs_tol=1e-12)
    return a==e


def review(parameters,candidate):
    from .auracast_product import validate,_values
    validate(parameters)
    if not isinstance(candidate,dict): raise ValueError("Auracast candidate object required")
    p=parameters;latency,skew=_values(p)
    raw=[("END_TO_END_LATENCY",latency,p["maximum_end_to_end_latency_ms"],"<=","REDUCE_BUFFER_CODEC_OR_TRANSPORT_LATENCY"),("INTER_RECEIVER_SYNC",skew,p["maximum_inter_receiver_skew_ms"],"<=","SHORTEN_RESYNC_INTERVAL_OR_IMPROVE_CLOCK_TRACKING"),("RECEIVER_DIVERSITY",p["receiver_count"],p["minimum_receiver_count"],">=","EXPAND_RECEIVER_COMPATIBILITY_MATRIX"),("PACKET_LOSS",p["packet_loss_fraction"],p["maximum_packet_loss_fraction"],"<=","REVISE_RADIO_COVERAGE_OR_PACKET_RECOVERY"),("RECEIVER_LEVEL_SPREAD",p["receiver_level_spread_db"],p["maximum_receiver_level_spread_db"],"<=","SEPARATE_RECEIVER_GAIN_FROM_BROADCAST_CONTENT_LEVEL")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"end_to_end_latency_ms":latency,"worst_resync_skew_ms":skew,"codec_profile":p["codec_profile"],"broadcast_profile":p["broadcast_profile"],"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED","audibility_verified":False,"interoperability_verified":False,"physical_receiver_matrix_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Transport jitter rather than hearing-device processing latency","Receiver gain variation rather than broadcast programme level","Coverage loss rather than codec incompatibility"],"next_discriminating_experiment":"RUN_MULTI_VENDOR_RECEIVER_LATENCY_SYNC_LEVEL_AND_COVERAGE_MATRIX_WITH_ACCESSIBILITY_REVIEW","model_assumptions":["Stage latencies add serially","Worst clock skew grows linearly until supplied resynchronization","Packet loss and level spread are supplied summary values"],"unresolved":["Codec implementation and radio scheduling distributions","Real multi-vendor interoperability and receiver diversity","Audibility, accessibility outcome and qualified Human approval"]}
    if set(candidate)!=set(expected): raise ValueError("exact Auracast assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"auracast-transport-sync","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,"observations":{"bounded_scope":"declared latency/clock/receiver/loss/level budget","unresolved":"live radio scheduling and multi-vendor accessibility"},"human_approval":False,"role_l3_awarded":False,"scope":"bounded Auracast transport report consistency only"}
