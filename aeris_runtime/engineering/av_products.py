"""Bounded soundbar and multichannel home-theater product decisions."""
from __future__ import annotations
import math

def _number(v,lo,hi):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError("finite supplied AV scalar outside bounded applicability")

SOUNDBAR={"crossover_sum_error_db":(0.0,100.0),"maximum_crossover_sum_error_db":(0.0,100.0),"subwoofer_delay_error_ms":(0.0,1000.0),"maximum_subwoofer_delay_error_ms":(0.0,1000.0),"wall_boundary_gain_db":(-100.0,100.0),"maximum_wall_boundary_gain_db":(-100.0,100.0),"dialogue_headroom_db":(-100.0,200.0),"minimum_dialogue_headroom_db":(-100.0,200.0),"lip_sync_error_ms":(0.0,10000.0),"maximum_lip_sync_error_ms":(0.0,10000.0),"seat_response_spread_db":(0.0,100.0),"maximum_seat_response_spread_db":(0.0,100.0)}

def validate_soundbar(p):
    expected=set(SOUNDBAR)|{"model","subwoofer_polarity","physical_soundbar_verified"}
    if not isinstance(p,dict) or set(p)!=expected:raise ValueError("exact soundbar crossover/wall budget required")
    if p["model"]!="SUPPLIED_SOUNDBAR_CROSSOVER_WALL_DIALOGUE_BUDGET":raise ValueError("unsupported soundbar model")
    if p["subwoofer_polarity"] not in {"NORMAL_DECLARED","INVERTED_DECLARED"}:raise ValueError("unsupported declared subwoofer polarity")
    if p["physical_soundbar_verified"] is not False:raise ValueError("physical soundbar acceptance requires external Evidence")
    for k,b in SOUNDBAR.items():_number(p[k],*b)

def analyze_soundbar(p):
    validate_soundbar(p);raw=[("CROSSOVER_SUM",p["crossover_sum_error_db"],p["maximum_crossover_sum_error_db"],"<=","REVISE_SOUNDBAR_SUB_POLARITY_PHASE_OR_CROSSOVER"),("SUBWOOFER_DELAY",p["subwoofer_delay_error_ms"],p["maximum_subwoofer_delay_error_ms"],"<=","ALIGN_SUBWOOFER_DELAY_AT_DECLARED_CROSSOVER"),("WALL_BOUNDARY_GAIN",p["wall_boundary_gain_db"],p["maximum_wall_boundary_gain_db"],"<=","REVISE_WALL_DISTANCE_OR_LOW_FREQUENCY_TUNING"),("DIALOGUE_HEADROOM",p["dialogue_headroom_db"],p["minimum_dialogue_headroom_db"],">=","REDUCE_DIALOGUE_EQ_OR_REVISE_OUTPUT_CHAIN"),("LIP_SYNC",p["lip_sync_error_ms"],p["maximum_lip_sync_error_ms"],"<=","REVISE_TRANSPORT_RENDER_OR_VIDEO_SYNC_DELAY"),("SEAT_RESPONSE_SPREAD",p["seat_response_spread_db"],p["maximum_seat_response_spread_db"],"<=","EXPAND_MULTI_SEAT_TUNING_AND_VALIDATION")]
    return _finish(p,"subwoofer_polarity",raw,["Wall loading rather than woofer defect","Transport delay rather than crossover phase","Sub polarity rather than dialogue-processing weakness"],"MEASURE_SOUNDBAR_SUB_TRANSFER_WALL_DISTANCE_LIP_SYNC_AND_DIALOGUE_HEADROOM_ACROSS_SEATS",["Crossover and wall terms are supplied scalar summaries","Lip sync excludes perceptual tolerance distribution","Seat spread uses a declared common level reference"],["Complex crossover/polarity transfer and room response","Transport/video timestamp path and listener variation","Physical system, dialogue quality and Human acceptance"],{"crossover_transfer_verified":False,"lip_sync_perceptually_verified":False,"physical_soundbar_verified":False})

THEATER={"channel_level_spread_db":(0.0,100.0),"maximum_channel_level_spread_db":(0.0,100.0),"polarity_error_count":(0,1000),"maximum_polarity_error_count":(0,1000),"channel_delay_error_ms":(0.0,1000.0),"maximum_channel_delay_error_ms":(0.0,1000.0),"seat_level_spread_db":(0.0,100.0),"maximum_seat_level_spread_db":(0.0,100.0),"subwoofer_crossover_error_db":(0.0,100.0),"maximum_subwoofer_crossover_error_db":(0.0,100.0),"calibration_position_count":(1,1000),"minimum_calibration_position_count":(1,1000)}

def validate_theater(p):
    expected=set(THEATER)|{"model","layout","physical_theater_verified"}
    if not isinstance(p,dict) or set(p)!=expected:raise ValueError("exact multichannel theater budget required")
    if p["model"]!="SUPPLIED_MULTICHANNEL_LEVEL_POLARITY_DELAY_BUDGET":raise ValueError("unsupported theater model")
    if p["layout"] not in {"FIVE_ONE_DECLARED","SEVEN_ONE_FOUR_DECLARED"}:raise ValueError("unsupported theater layout")
    if p["physical_theater_verified"] is not False:raise ValueError("physical theater acceptance requires external Evidence")
    for k,b in THEATER.items():_number(p[k],*b)
    for k in ("polarity_error_count","maximum_polarity_error_count","calibration_position_count","minimum_calibration_position_count"):
        if not isinstance(p[k],int):raise ValueError("integer theater count required")

def analyze_theater(p):
    validate_theater(p);raw=[("CHANNEL_LEVEL_MATCH",p["channel_level_spread_db"],p["maximum_channel_level_spread_db"],"<=","REMATCH_CHANNEL_LEVELS_WITH_COMMON_REFERENCE"),("CHANNEL_POLARITY",p["polarity_error_count"],p["maximum_polarity_error_count"],"<=","CORRECT_WIRING_OR_RENDER_POLARITY_BEFORE_EQ"),("CHANNEL_DELAY",p["channel_delay_error_ms"],p["maximum_channel_delay_error_ms"],"<=","REALIGN_CHANNEL_DISTANCE_AND_PROCESSING_DELAY"),("SEAT_REGION_SPREAD",p["seat_level_spread_db"],p["maximum_seat_level_spread_db"],"<=","REVISE_MULTI_SEAT_LEVEL_AND_DELAY_OPTIMIZATION"),("SUBWOOFER_CROSSOVER",p["subwoofer_crossover_error_db"],p["maximum_subwoofer_crossover_error_db"],"<=","REVISE_SUB_POLARITY_DELAY_OR_CROSSOVER"),("CALIBRATION_POSITION_COVERAGE",p["calibration_position_count"],p["minimum_calibration_position_count"],">=","EXPAND_CALIBRATION_MICROPHONE_POSITION_MATRIX")]
    return _finish(p,"layout",raw,["Room mode rather than subwoofer delay","Miswired polarity rather than HRTF/rendering defect","Single-seat optimization rather than channel mismatch"],"MEASURE_CHANNEL_LEVEL_POLARITY_DELAY_AND_SUB_TRANSFER_OVER_THE_DECLARED_SEAT_REGION",["All channels use a supplied common level/time reference","Seat spread is a scalar regional summary","Calibration position count does not establish representativeness"],["Complex room/channel transfer and calibration-mic uncertainty","Rendering metadata and wiring provenance","Physical multichannel system and listener acceptance"],{"wiring_verified":False,"seat_region_verified":False,"physical_theater_verified":False})

def _finish(p,label,raw,counters,experiment,assumptions,unresolved,claims):
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {label:p[label],"checks":checks,"required_revisions":[c["on_failure"] for c in checks if not c["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(c["passed"] for c in checks) else "DESIGN_REVISION_REQUIRED",**claims,"physical_measurement_verified":False,"counter_hypotheses":counters,"next_discriminating_experiment":experiment,"model_assumptions":assumptions,"unresolved":unresolved}
