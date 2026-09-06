"""Independent reviews for bounded interactive-device product decisions."""
from __future__ import annotations
import math

def _same(a,e):
    if isinstance(e,dict):return isinstance(a,dict) and set(a)==set(e) and all(_same(a[k],v) for k,v in e.items())
    if isinstance(e,list):return isinstance(a,list) and len(a)==len(e) and all(_same(x,y) for x,y in zip(a,e))
    if isinstance(e,bool) or e is None:return a is e
    if isinstance(e,(int,float)):return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and math.isclose(a,e,rel_tol=1e-10,abs_tol=1e-12)
    return a==e

def review_gaming(p,candidate):
    from .personal_device_products import validate_gaming,_gaming_values
    validate_gaming(p);latency=_gaming_values(p)
    raw=[("SIDETONE_LATENCY",latency,p["maximum_sidetone_latency_ms"],"<=","REDUCE_CAPTURE_PROCESSING_OR_PLAYBACK_BUFFER"),("BOOM_DISTANCE_MINIMUM",p["boom_mic_distance_m"],p["minimum_boom_distance_m"],">=","MOVE_BOOM_AWAY_FROM_PLOSIVE_ZONE"),("BOOM_DISTANCE_MAXIMUM",p["boom_mic_distance_m"],p["maximum_boom_distance_m"],"<=","MOVE_BOOM_TOWARD_NEARFIELD_SPEECH"),("PLAYBACK_CROSSTALK",p["speaker_to_mic_crosstalk_db"],p["maximum_crosstalk_db"],"<=","REVISE_EARCUP_ISOLATION_BOOM_OR_AEC_PATH"),("VOICE_SNR",p["voice_snr_db"],p["minimum_voice_snr_db"],">=","REVISE_BOOM_POSITION_NOISE_REDUCTION_OR_GAIN"),("OUTPUT_HEADROOM",p["output_headroom_db"],p["minimum_output_headroom_db"],">=","REDUCE_PLAYBACK_GAIN_OR_REVISE_OUTPUT_CHAIN")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"sidetone_latency_ms":latency,"microphone_topology":p["microphone_topology"],"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED","plosive_performance_verified":False,"communication_quality_verified":False,"physical_call_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Boom distance rather than noise-reduction defect","Playback leakage rather than network echo","Local buffering rather than network latency"],"next_discriminating_experiment":"MEASURE_LOCAL_SIDETONE_BOOM_PLOSIVE_CROSSTALK_AND_CALL_QUALITY_ACROSS_USERS","model_assumptions":["Local sidetone stages add serially","Boom distance is a supplied scalar proxy","Crosstalk, SNR and headroom share a declared operating state"],"unresolved":["Plosive directivity and user boom placement distribution","Codec/network path and nonlinear AEC behavior","Physical call quality and qualified Human acceptance"]}
    return _finish("gaming-communication-latency",candidate,expected,"sidetone/boom/crosstalk/SNR/headroom")

def review_smartphone(p,candidate):
    from .personal_device_products import validate_smartphone
    validate_smartphone(p)
    raw=[("HAND_BLOCKAGE",p["hand_blockage_loss_db"],p["maximum_hand_blockage_loss_db"],"<=","REVISE_PORT_DISTRIBUTION_OR_ORIENTATION_ROUTING"),("WATER_MESH_LOSS",p["water_mesh_loss_db"],p["maximum_water_mesh_loss_db"],"<=","REVISE_MESH_PORT_OR_GAIN_BUDGET"),("ECHO_COUPLING",p["speaker_to_mic_echo_coupling_db"],p["maximum_echo_coupling_db"],"<=","REVISE_SPEAKER_MIC_ISOLATION_OR_AEC_RANGE"),("ORIENTATION_COVERAGE",p["orientation_count"],p["minimum_orientation_count"],">=","EXPAND_HANDHELD_VIDEO_SPEAKERPHONE_ORIENTATION_MATRIX"),("BOTTOM_SPEAKER_EXCURSION",p["bottom_speaker_peak_excursion_mm"],p["safe_bottom_speaker_excursion_mm"],"<=","LIMIT_BASS_DRIVE_OR_REVISE_BOTTOM_SPEAKER"),("HANDHELD_CALL_SNR",p["handheld_call_snr_db"],p["minimum_handheld_call_snr_db"],">=","REVISE_MIC_SELECTION_PORT_OR_NOISE_REDUCTION")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"port_protection":p["port_protection"],"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED","mesh_transfer_verified":False,"hand_population_verified":False,"aec_verified":False,"physical_handset_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Hand blockage rather than speaker defect","Water mesh loss rather than capsule sensitivity shift","Mechanical coupling rather than AEC algorithm regression"],"next_discriminating_experiment":"MEASURE_PORT_MESH_HAND_ORIENTATION_ECHO_AND_EXCURSION_ON_REFERENCED_HANDSETS","model_assumptions":["Blockage and mesh losses are supplied scalar maxima","Echo coupling uses one declared level convention","Orientation count is coverage metadata, not a population result"],"unresolved":["Frequency-dependent hand/mesh transfer and unit variation","Nonlinear speaker excursion and time-varying echo path","Physical handset, call quality and qualified Human acceptance"]}
    return _finish("smartphone-port-mesh-echo",candidate,expected,"hand/mesh/echo/orientation/excursion/SNR")

def _finish(domain,candidate,expected,scope):
    if not isinstance(candidate,dict) or set(candidate)!=set(expected):raise ValueError("exact product assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":domain,"decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,"observations":{"bounded_scope":scope,"unresolved":"physical product distribution and Human acceptance"},"human_approval":False,"role_l3_awarded":False,"scope":"bounded product report consistency only"}
