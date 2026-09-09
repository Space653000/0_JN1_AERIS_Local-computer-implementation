"""Independent exact-output reviewers for AV product budgets."""
from __future__ import annotations
import math

def _same(a,e):
    if isinstance(e,dict):return isinstance(a,dict) and set(a)==set(e) and all(_same(a[k],v) for k,v in e.items())
    if isinstance(e,list):return isinstance(a,list) and len(a)==len(e) and all(_same(x,y) for x,y in zip(a,e))
    if isinstance(e,bool) or e is None:return a is e
    if isinstance(e,(int,float)):return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and math.isclose(a,e,rel_tol=1e-10,abs_tol=1e-12)
    return a==e

def review_soundbar(p,candidate):
    from .av_products import validate_soundbar
    validate_soundbar(p);raw=[("CROSSOVER_SUM",p["crossover_sum_error_db"],p["maximum_crossover_sum_error_db"],"<=","REVISE_SOUNDBAR_SUB_POLARITY_PHASE_OR_CROSSOVER"),("SUBWOOFER_DELAY",p["subwoofer_delay_error_ms"],p["maximum_subwoofer_delay_error_ms"],"<=","ALIGN_SUBWOOFER_DELAY_AT_DECLARED_CROSSOVER"),("WALL_BOUNDARY_GAIN",p["wall_boundary_gain_db"],p["maximum_wall_boundary_gain_db"],"<=","REVISE_WALL_DISTANCE_OR_LOW_FREQUENCY_TUNING"),("DIALOGUE_HEADROOM",p["dialogue_headroom_db"],p["minimum_dialogue_headroom_db"],">=","REDUCE_DIALOGUE_EQ_OR_REVISE_OUTPUT_CHAIN"),("LIP_SYNC",p["lip_sync_error_ms"],p["maximum_lip_sync_error_ms"],"<=","REVISE_TRANSPORT_RENDER_OR_VIDEO_SYNC_DELAY"),("SEAT_RESPONSE_SPREAD",p["seat_response_spread_db"],p["maximum_seat_response_spread_db"],"<=","EXPAND_MULTI_SEAT_TUNING_AND_VALIDATION")]
    expected=_expected(p,"subwoofer_polarity",raw,["Wall loading rather than woofer defect","Transport delay rather than crossover phase","Sub polarity rather than dialogue-processing weakness"],"MEASURE_SOUNDBAR_SUB_TRANSFER_WALL_DISTANCE_LIP_SYNC_AND_DIALOGUE_HEADROOM_ACROSS_SEATS",["Crossover and wall terms are supplied scalar summaries","Lip sync excludes perceptual tolerance distribution","Seat spread uses a declared common level reference"],["Complex crossover/polarity transfer and room response","Transport/video timestamp path and listener variation","Physical system, dialogue quality and Human acceptance"],{"crossover_transfer_verified":False,"lip_sync_perceptually_verified":False,"physical_soundbar_verified":False})
    return _finish("soundbar-crossover-wall-dialogue",candidate,expected,"crossover/sub/wall/dialogue/lip-sync/seat")

def review_theater(p,candidate):
    from .av_products import validate_theater
    validate_theater(p);raw=[("CHANNEL_LEVEL_MATCH",p["channel_level_spread_db"],p["maximum_channel_level_spread_db"],"<=","REMATCH_CHANNEL_LEVELS_WITH_COMMON_REFERENCE"),("CHANNEL_POLARITY",p["polarity_error_count"],p["maximum_polarity_error_count"],"<=","CORRECT_WIRING_OR_RENDER_POLARITY_BEFORE_EQ"),("CHANNEL_DELAY",p["channel_delay_error_ms"],p["maximum_channel_delay_error_ms"],"<=","REALIGN_CHANNEL_DISTANCE_AND_PROCESSING_DELAY"),("SEAT_REGION_SPREAD",p["seat_level_spread_db"],p["maximum_seat_level_spread_db"],"<=","REVISE_MULTI_SEAT_LEVEL_AND_DELAY_OPTIMIZATION"),("SUBWOOFER_CROSSOVER",p["subwoofer_crossover_error_db"],p["maximum_subwoofer_crossover_error_db"],"<=","REVISE_SUB_POLARITY_DELAY_OR_CROSSOVER"),("CALIBRATION_POSITION_COVERAGE",p["calibration_position_count"],p["minimum_calibration_position_count"],">=","EXPAND_CALIBRATION_MICROPHONE_POSITION_MATRIX")]
    expected=_expected(p,"layout",raw,["Room mode rather than subwoofer delay","Miswired polarity rather than HRTF/rendering defect","Single-seat optimization rather than channel mismatch"],"MEASURE_CHANNEL_LEVEL_POLARITY_DELAY_AND_SUB_TRANSFER_OVER_THE_DECLARED_SEAT_REGION",["All channels use a supplied common level/time reference","Seat spread is a scalar regional summary","Calibration position count does not establish representativeness"],["Complex room/channel transfer and calibration-mic uncertainty","Rendering metadata and wiring provenance","Physical multichannel system and listener acceptance"],{"wiring_verified":False,"seat_region_verified":False,"physical_theater_verified":False})
    return _finish("home-theater-level-polarity-delay",candidate,expected,"channel-level/polarity/delay/seat/sub/calibration")

def _expected(p,label,raw,counters,experiment,assumptions,unresolved,claims):
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {label:p[label],"checks":checks,"required_revisions":[c["on_failure"] for c in checks if not c["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(c["passed"] for c in checks) else "DESIGN_REVISION_REQUIRED",**claims,"physical_measurement_verified":False,"counter_hypotheses":counters,"next_discriminating_experiment":experiment,"model_assumptions":assumptions,"unresolved":unresolved}

def _finish(domain,candidate,expected,scope):
    if not isinstance(candidate,dict) or set(candidate)!=set(expected):raise ValueError("exact AV assertions required")
    diffs=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":domain,"decision":"CHANGES_REQUIRED" if diffs else "BOUNDED_REVIEW_ACCEPT","disagreements":diffs,"observations":{"bounded_scope":scope,"unresolved":"physical product distribution and Human acceptance"},"human_approval":False,"role_l3_awarded":False,"scope":"bounded AV report consistency only"}
