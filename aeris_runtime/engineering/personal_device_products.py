"""Bounded product decisions for interactive headset and handheld audio."""
from __future__ import annotations
import math


def _number(value,low,high):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError("finite declared product value outside bounded applicability")


GAMING_SCALARS={"capture_buffer_ms":(0.0,1000.0),"sidetone_processing_ms":(0.0,1000.0),"playback_buffer_ms":(0.0,1000.0),"maximum_sidetone_latency_ms":(0.0,3000.0),"boom_mic_distance_m":(0.0,2.0),"minimum_boom_distance_m":(0.0,2.0),"maximum_boom_distance_m":(0.0,2.0),"speaker_to_mic_crosstalk_db":(-200.0,100.0),"maximum_crosstalk_db":(-200.0,100.0),"voice_snr_db":(-100.0,200.0),"minimum_voice_snr_db":(-100.0,200.0),"output_headroom_db":(-100.0,200.0),"minimum_output_headroom_db":(-100.0,200.0)}


def validate_gaming(p):
    expected=set(GAMING_SCALARS)|{"model","microphone_topology","physical_call_verified"}
    if not isinstance(p,dict) or set(p)!=expected: raise ValueError("exact gaming headset budget required")
    if p["model"]!="SUPPLIED_GAMING_HEADSET_COMMUNICATION_BUDGET": raise ValueError("unsupported gaming-headset model")
    if p["microphone_topology"] not in {"BOOM_MICROPHONE","SHORT_NEARFIELD_ARRAY"}: raise ValueError("unsupported gaming microphone topology")
    if p["physical_call_verified"] is not False: raise ValueError("physical communication acceptance requires external Evidence")
    for k,b in GAMING_SCALARS.items():_number(p[k],*b)
    if p["minimum_boom_distance_m"]>p["maximum_boom_distance_m"]: raise ValueError("invalid boom-distance interval")


def _gaming_values(p):return p["capture_buffer_ms"]+p["sidetone_processing_ms"]+p["playback_buffer_ms"]


def analyze_gaming(p):
    validate_gaming(p);latency=_gaming_values(p)
    raw=[("SIDETONE_LATENCY",latency,p["maximum_sidetone_latency_ms"],"<=","REDUCE_CAPTURE_PROCESSING_OR_PLAYBACK_BUFFER"),("BOOM_DISTANCE_MINIMUM",p["boom_mic_distance_m"],p["minimum_boom_distance_m"],">=","MOVE_BOOM_AWAY_FROM_PLOSIVE_ZONE"),("BOOM_DISTANCE_MAXIMUM",p["boom_mic_distance_m"],p["maximum_boom_distance_m"],"<=","MOVE_BOOM_TOWARD_NEARFIELD_SPEECH"),("PLAYBACK_CROSSTALK",p["speaker_to_mic_crosstalk_db"],p["maximum_crosstalk_db"],"<=","REVISE_EARCUP_ISOLATION_BOOM_OR_AEC_PATH"),("VOICE_SNR",p["voice_snr_db"],p["minimum_voice_snr_db"],">=","REVISE_BOOM_POSITION_NOISE_REDUCTION_OR_GAIN"),("OUTPUT_HEADROOM",p["output_headroom_db"],p["minimum_output_headroom_db"],">=","REDUCE_PLAYBACK_GAIN_OR_REVISE_OUTPUT_CHAIN")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"sidetone_latency_ms":latency,"microphone_topology":p["microphone_topology"],"checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED","plosive_performance_verified":False,"communication_quality_verified":False,"physical_call_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Boom distance rather than noise-reduction defect","Playback leakage rather than network echo","Local buffering rather than network latency"],"next_discriminating_experiment":"MEASURE_LOCAL_SIDETONE_BOOM_PLOSIVE_CROSSTALK_AND_CALL_QUALITY_ACROSS_USERS","model_assumptions":["Local sidetone stages add serially","Boom distance is a supplied scalar proxy","Crosstalk, SNR and headroom share a declared operating state"],"unresolved":["Plosive directivity and user boom placement distribution","Codec/network path and nonlinear AEC behavior","Physical call quality and qualified Human acceptance"]}


PHONE_SCALARS={"hand_blockage_loss_db":(0.0,100.0),"maximum_hand_blockage_loss_db":(0.0,100.0),"water_mesh_loss_db":(0.0,100.0),"maximum_water_mesh_loss_db":(0.0,100.0),"speaker_to_mic_echo_coupling_db":(-200.0,200.0),"maximum_echo_coupling_db":(-200.0,200.0),"orientation_count":(1,1000),"minimum_orientation_count":(1,1000),"bottom_speaker_peak_excursion_mm":(0.0,100.0),"safe_bottom_speaker_excursion_mm":(0.001,100.0),"handheld_call_snr_db":(-100.0,200.0),"minimum_handheld_call_snr_db":(-100.0,200.0)}


def validate_smartphone(p):
    expected=set(PHONE_SCALARS)|{"model","port_protection","physical_handset_verified"}
    if not isinstance(p,dict) or set(p)!=expected:raise ValueError("exact smartphone acoustic budget required")
    if p["model"]!="SUPPLIED_SMARTPHONE_HAND_BLOCK_MESH_ECHO_BUDGET":raise ValueError("unsupported smartphone model")
    if p["port_protection"] not in {"WATER_MESH_DECLARED","OPEN_PORT_DECLARED"}:raise ValueError("unsupported smartphone port protection")
    if p["physical_handset_verified"] is not False:raise ValueError("physical handset acceptance requires external Evidence")
    for k,b in PHONE_SCALARS.items():_number(p[k],*b)
    if not isinstance(p["orientation_count"],int) or not isinstance(p["minimum_orientation_count"],int):raise ValueError("integer orientation count required")


def analyze_smartphone(p):
    validate_smartphone(p)
    raw=[("HAND_BLOCKAGE",p["hand_blockage_loss_db"],p["maximum_hand_blockage_loss_db"],"<=","REVISE_PORT_DISTRIBUTION_OR_ORIENTATION_ROUTING"),("WATER_MESH_LOSS",p["water_mesh_loss_db"],p["maximum_water_mesh_loss_db"],"<=","REVISE_MESH_PORT_OR_GAIN_BUDGET"),("ECHO_COUPLING",p["speaker_to_mic_echo_coupling_db"],p["maximum_echo_coupling_db"],"<=","REVISE_SPEAKER_MIC_ISOLATION_OR_AEC_RANGE"),("ORIENTATION_COVERAGE",p["orientation_count"],p["minimum_orientation_count"],">=","EXPAND_HANDHELD_VIDEO_SPEAKERPHONE_ORIENTATION_MATRIX"),("BOTTOM_SPEAKER_EXCURSION",p["bottom_speaker_peak_excursion_mm"],p["safe_bottom_speaker_excursion_mm"],"<=","LIMIT_BASS_DRIVE_OR_REVISE_BOTTOM_SPEAKER"),("HANDHELD_CALL_SNR",p["handheld_call_snr_db"],p["minimum_handheld_call_snr_db"],">=","REVISE_MIC_SELECTION_PORT_OR_NOISE_REDUCTION")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"port_protection":p["port_protection"],"checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED","mesh_transfer_verified":False,"hand_population_verified":False,"aec_verified":False,"physical_handset_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Hand blockage rather than speaker defect","Water mesh loss rather than capsule sensitivity shift","Mechanical coupling rather than AEC algorithm regression"],"next_discriminating_experiment":"MEASURE_PORT_MESH_HAND_ORIENTATION_ECHO_AND_EXCURSION_ON_REFERENCED_HANDSETS","model_assumptions":["Blockage and mesh losses are supplied scalar maxima","Echo coupling uses one declared level convention","Orientation count is coverage metadata, not a population result"],"unresolved":["Frequency-dependent hand/mesh transfer and unit variation","Nonlinear speaker excursion and time-varying echo path","Physical handset, call quality and qualified Human acceptance"]}
