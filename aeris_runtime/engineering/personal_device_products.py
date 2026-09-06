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


TABLET_SCALARS={"orientation_mode_count":(1,1000),"minimum_orientation_mode_count":(1,1000),"blocked_edge_port_count":(0,1000),"maximum_blocked_edge_port_count":(0,1000),"case_port_clearance_mm":(0.0,100.0),"minimum_case_port_clearance_mm":(0.0,100.0),"table_reflection_delay_ms":(0.0,1000.0),"minimum_table_reflection_delay_ms":(0.0,1000.0),"stereo_balance_error_db":(0.0,100.0),"maximum_stereo_balance_error_db":(0.0,100.0),"array_steering_error_deg":(0.0,180.0),"maximum_array_steering_error_deg":(0.0,180.0)}


def validate_tablet(p):
    expected=set(TABLET_SCALARS)|{"model","placement_set","physical_tablet_verified"}
    if not isinstance(p,dict) or set(p)!=expected:raise ValueError("exact tablet orientation budget required")
    if p["model"]!="SUPPLIED_TABLET_ORIENTATION_CASE_TABLE_BUDGET":raise ValueError("unsupported tablet model")
    if p["placement_set"] not in {"PORTRAIT_LANDSCAPE_TABLE","HANDHELD_AND_TABLE"}:raise ValueError("unsupported tablet placement set")
    if p["physical_tablet_verified"] is not False:raise ValueError("physical tablet acceptance requires external Evidence")
    for k,b in TABLET_SCALARS.items():_number(p[k],*b)
    for k in ("orientation_mode_count","minimum_orientation_mode_count","blocked_edge_port_count","maximum_blocked_edge_port_count"):
        if not isinstance(p[k],int):raise ValueError("integer tablet coverage count required")


def analyze_tablet(p):
    validate_tablet(p)
    raw=[("ORIENTATION_MODE_COVERAGE",p["orientation_mode_count"],p["minimum_orientation_mode_count"],">=","EXPAND_PORTRAIT_LANDSCAPE_AND_TABLE_MATRIX"),("CASE_BLOCKED_EDGE_PORTS",p["blocked_edge_port_count"],p["maximum_blocked_edge_port_count"],"<=","REVISE_CASE_CUTOUT_OR_EDGE_PORT_ROUTING"),("CASE_PORT_CLEARANCE",p["case_port_clearance_mm"],p["minimum_case_port_clearance_mm"],">=","INCREASE_CASE_TO_PORT_CLEARANCE"),("TABLE_REFLECTION_DELAY",p["table_reflection_delay_ms"],p["minimum_table_reflection_delay_ms"],">=","REVISE_TABLE_PLACEMENT_ARRAY_STEERING_OR_GATING"),("STEREO_BALANCE",p["stereo_balance_error_db"],p["maximum_stereo_balance_error_db"],"<=","REMAP_OR_EQUALIZE_ORIENTATION_DEPENDENT_EDGE_SPEAKERS"),("ARRAY_STEERING",p["array_steering_error_deg"],p["maximum_array_steering_error_deg"],"<=","RECALCULATE_ORIENTATION_AND_TABLE_REFLECTION_STEERING")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"placement_set":p["placement_set"],"checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED","case_transfer_verified":False,"table_reflection_verified":False,"orientation_population_verified":False,"physical_tablet_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Orientation mapping rather than speaker mismatch","Case interference rather than capsule variation","Table reflection rather than beamformer defect"],"next_discriminating_experiment":"MEASURE_CASE_PORT_TRANSFER_AND_ARRAY_RESPONSE_IN_PORTRAIT_LANDSCAPE_HANDHELD_AND_TABLE_STATES","model_assumptions":["Placement modes are supplied categorical coverage","Port clearance and reflection delay are scalar design proxies","Balance and steering errors share a declared reference state"],"unresolved":["Frequency-dependent case and table transfer","User grip and case population distribution","Physical tablet, speech quality and qualified Human acceptance"]}


LAPTOP_SCALARS={"fan_harmonic_capture_db":(-200.0,200.0),"maximum_fan_harmonic_capture_db":(-200.0,200.0),"hinge_angle_count":(1,1000),"minimum_hinge_angle_count":(1,1000),"array_transfer_spread_db":(0.0,100.0),"maximum_array_transfer_spread_db":(0.0,100.0),"keyboard_body_coupling_db":(-200.0,200.0),"maximum_keyboard_body_coupling_db":(-200.0,200.0),"speaker_headroom_db":(-100.0,200.0),"minimum_speaker_headroom_db":(-100.0,200.0),"aec_reference_alignment_ms":(0.0,1000.0),"maximum_aec_reference_alignment_ms":(0.0,1000.0)}


def validate_laptop(p):
    expected=set(LAPTOP_SCALARS)|{"model","fan_operating_set","physical_laptop_verified"}
    if not isinstance(p,dict) or set(p)!=expected:raise ValueError("exact laptop fan/hinge budget required")
    if p["model"]!="SUPPLIED_LAPTOP_FAN_HINGE_COUPLING_BUDGET":raise ValueError("unsupported laptop model")
    if p["fan_operating_set"] not in {"IDLE_NOMINAL_TURBO","NOMINAL_AND_TURBO"}:raise ValueError("unsupported fan operating set")
    if p["physical_laptop_verified"] is not False:raise ValueError("physical laptop acceptance requires external Evidence")
    for k,b in LAPTOP_SCALARS.items():_number(p[k],*b)
    if not isinstance(p["hinge_angle_count"],int) or not isinstance(p["minimum_hinge_angle_count"],int):raise ValueError("integer hinge coverage required")


def analyze_laptop(p):
    validate_laptop(p)
    raw=[("FAN_HARMONIC_CAPTURE",p["fan_harmonic_capture_db"],p["maximum_fan_harmonic_capture_db"],"<=","REVISE_FAN_STATE_CAPTURE_NOTCH_OR_MIC_PLACEMENT"),("HINGE_ANGLE_COVERAGE",p["hinge_angle_count"],p["minimum_hinge_angle_count"],">=","EXPAND_HINGE_ANGLE_TRANSFER_MATRIX"),("ARRAY_TRANSFER_SPREAD",p["array_transfer_spread_db"],p["maximum_array_transfer_spread_db"],"<=","REVISE_BEZEL_ARRAY_OR_HINGE_DEPENDENT_PROCESSING"),("KEYBOARD_BODY_COUPLING",p["keyboard_body_coupling_db"],p["maximum_keyboard_body_coupling_db"],"<=","ISOLATE_KEYBOARD_BODY_PATH_BEFORE_AEC_RETUNING"),("SPEAKER_HEADROOM",p["speaker_headroom_db"],p["minimum_speaker_headroom_db"],">=","REDUCE_OUTPUT_GAIN_OR_REVISE_SPEAKER_CHAIN"),("AEC_REFERENCE_ALIGNMENT",p["aec_reference_alignment_ms"],p["maximum_aec_reference_alignment_ms"],"<=","ALIGN_PLAYBACK_REFERENCE_BEFORE_ECHO_ADAPTATION")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"fan_operating_set":p["fan_operating_set"],"checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED","fan_path_verified":False,"hinge_transfer_verified":False,"aec_verified":False,"physical_laptop_verified":False,"physical_measurement_verified":False,"counter_hypotheses":["Structural coupling rather than AEC failure","Thermal policy rather than microphone defect","Hinge transfer rather than fixed array calibration error"],"next_discriminating_experiment":"MEASURE_FAN_HARMONICS_KEYBOARD_COUPLING_AND_BEZEL_ARRAY_TRANSFER_ACROSS_HINGE_AND_THERMAL_STATES","model_assumptions":["Fan harmonic and coupling values use one declared reference","Hinge count is coverage metadata, not continuous transfer","Headroom and AEC alignment are supplied scalar budgets"],"unresolved":["Continuous hinge-angle acoustic transfer and fan order tracking","Keyboard/body modal paths and thermal policy variation","Physical laptop, call quality and qualified Human acceptance"]}
