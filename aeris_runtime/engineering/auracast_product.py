"""Bounded R047 Auracast latency, receiver-diversity and sync screening."""
from __future__ import annotations

import math


SCALARS={
    "transmitter_buffer_ms":(0.0,10000.0),"codec_frame_ms":(0.0,1000.0),"transport_latency_ms":(0.0,10000.0),
    "receiver_buffer_ms":(0.0,10000.0),"receiver_processing_ms":(0.0,10000.0),"maximum_end_to_end_latency_ms":(0.0,30000.0),
    "maximum_receiver_clock_offset_ppm":(0.0,100000.0),"resync_interval_s":(0.001,86400.0),"maximum_inter_receiver_skew_ms":(0.0,10000.0),
    "receiver_count":(1,100000),"minimum_receiver_count":(1,100000),"packet_loss_fraction":(0.0,1.0),"maximum_packet_loss_fraction":(0.0,1.0),
    "receiver_level_spread_db":(0.0,100.0),"maximum_receiver_level_spread_db":(0.0,100.0),
}


def _number(value,low,high):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError("finite declared Auracast value outside bounded applicability")


def validate(parameters):
    expected=set(SCALARS)|{"model","codec_profile","broadcast_profile","audibility_verified","interoperability_verified"}
    if not isinstance(parameters,dict) or set(parameters)!=expected: raise ValueError("exact supplied Auracast budget required")
    if parameters["model"]!="SUPPLIED_AURACAST_LATENCY_SYNC_BUDGET": raise ValueError("unsupported Auracast model")
    if parameters["codec_profile"] not in {"LC3_DECLARED","VENDOR_LC3_DECLARED"}: raise ValueError("unsupported declared codec profile")
    if parameters["broadcast_profile"] not in {"PUBLIC_ASSISTIVE_LISTENING","PRIVATE_ASSISTIVE_LISTENING"}: raise ValueError("unsupported broadcast profile")
    if parameters["audibility_verified"] is not False or parameters["interoperability_verified"] is not False:
        raise ValueError("audibility and interoperability require external receiver Evidence")
    for key,bounds in SCALARS.items(): _number(parameters[key],*bounds)
    for key in ("receiver_count","minimum_receiver_count"):
        if not isinstance(parameters[key],int): raise ValueError("integer receiver-count contract required")


def _values(p):
    latency=sum(p[k] for k in ("transmitter_buffer_ms","codec_frame_ms","transport_latency_ms","receiver_buffer_ms","receiver_processing_ms"))
    skew=p["maximum_receiver_clock_offset_ppm"]*p["resync_interval_s"]/1000.0
    return latency,skew


def analyze(parameters):
    validate(parameters);p=parameters;latency,skew=_values(p)
    raw=[
        ("END_TO_END_LATENCY",latency,p["maximum_end_to_end_latency_ms"],"<=","REDUCE_BUFFER_CODEC_OR_TRANSPORT_LATENCY"),
        ("INTER_RECEIVER_SYNC",skew,p["maximum_inter_receiver_skew_ms"],"<=","SHORTEN_RESYNC_INTERVAL_OR_IMPROVE_CLOCK_TRACKING"),
        ("RECEIVER_DIVERSITY",p["receiver_count"],p["minimum_receiver_count"],">=","EXPAND_RECEIVER_COMPATIBILITY_MATRIX"),
        ("PACKET_LOSS",p["packet_loss_fraction"],p["maximum_packet_loss_fraction"],"<=","REVISE_RADIO_COVERAGE_OR_PACKET_RECOVERY"),
        ("RECEIVER_LEVEL_SPREAD",p["receiver_level_spread_db"],p["maximum_receiver_level_spread_db"],"<=","SEPARATE_RECEIVER_GAIN_FROM_BROADCAST_CONTENT_LEVEL")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"end_to_end_latency_ms":latency,"worst_resync_skew_ms":skew,"codec_profile":p["codec_profile"],"broadcast_profile":p["broadcast_profile"],
            "checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],
            "disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED",
            "audibility_verified":False,"interoperability_verified":False,"physical_receiver_matrix_verified":False,"physical_measurement_verified":False,
            "counter_hypotheses":["Transport jitter rather than hearing-device processing latency","Receiver gain variation rather than broadcast programme level","Coverage loss rather than codec incompatibility"],
            "next_discriminating_experiment":"RUN_MULTI_VENDOR_RECEIVER_LATENCY_SYNC_LEVEL_AND_COVERAGE_MATRIX_WITH_ACCESSIBILITY_REVIEW",
            "model_assumptions":["Stage latencies add serially","Worst clock skew grows linearly until supplied resynchronization","Packet loss and level spread are supplied summary values"],
            "unresolved":["Codec implementation and radio scheduling distributions","Real multi-vendor interoperability and receiver diversity","Audibility, accessibility outcome and qualified Human approval"]}
