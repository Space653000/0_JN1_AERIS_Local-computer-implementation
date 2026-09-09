"""Bounded monitor/AIO and smart-speaker product architecture decisions."""
from __future__ import annotations

import math


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite supplied product scalar outside bounded applicability")


MONITOR_SCALARS={"power_supply_hum_db":(-200.0,200.0),"maximum_power_supply_hum_db":(-200.0,200.0),"bezel_array_spread_db":(0.0,100.0),"maximum_bezel_array_spread_db":(0.0,100.0),"desk_reflection_delay_ms":(0.0,1000.0),"minimum_desk_reflection_delay_ms":(0.0,1000.0),"usb_audio_latency_ms":(0.0,10000.0),"maximum_usb_audio_latency_ms":(0.0,10000.0),"display_orientation_count":(1,1000),"minimum_display_orientation_count":(1,1000),"echo_reference_alignment_ms":(0.0,1000.0),"maximum_echo_reference_alignment_ms":(0.0,1000.0)}


def validate_monitor(p):
    expected=set(MONITOR_SCALARS)|{"model","usb_mode","physical_monitor_verified"}
    if not isinstance(p,dict) or set(p)!=expected:raise ValueError("exact monitor/AIO conference budget required")
    if p["model"]!="SUPPLIED_MONITOR_AIO_CONFERENCE_BUDGET":raise ValueError("unsupported monitor/AIO model")
    if p["usb_mode"] not in {"USB_AUDIO_SYNCHRONOUS_DECLARED","USB_AUDIO_ASYNCHRONOUS_DECLARED"}:raise ValueError("unsupported USB mode")
    if p["physical_monitor_verified"] is not False:raise ValueError("physical monitor acceptance requires external Evidence")
    for key,bounds in MONITOR_SCALARS.items():_number(p[key],*bounds)
    if not isinstance(p["display_orientation_count"],int) or not isinstance(p["minimum_display_orientation_count"],int):raise ValueError("integer display orientation count required")


def analyze_monitor(p):
    validate_monitor(p)
    raw=[("POWER_SUPPLY_HUM",p["power_supply_hum_db"],p["maximum_power_supply_hum_db"],"<=","ISOLATE_GROUND_OR_POWER_COUPLING_BEFORE_DIGITAL_NOTCH"),("BEZEL_ARRAY_SPREAD",p["bezel_array_spread_db"],p["maximum_bezel_array_spread_db"],"<=","REVISE_BEZEL_PORT_OR_ARRAY_EQUALIZATION"),("DESK_REFLECTION_DELAY",p["desk_reflection_delay_ms"],p["minimum_desk_reflection_delay_ms"],">=","REVISE_DESK_DISTANCE_OR_REFLECTION_GATING"),("USB_AUDIO_LATENCY",p["usb_audio_latency_ms"],p["maximum_usb_audio_latency_ms"],"<=","REVISE_USB_BUFFER_SCHEDULING_OR_CLOCK_POLICY"),("DISPLAY_ORIENTATION_COVERAGE",p["display_orientation_count"],p["minimum_display_orientation_count"],">=","EXPAND_DISPLAY_TILT_HEIGHT_AND_DESK_MATRIX"),("ECHO_REFERENCE_ALIGNMENT",p["echo_reference_alignment_ms"],p["maximum_echo_reference_alignment_ms"],"<=","ALIGN_USB_PLAYBACK_REFERENCE_BEFORE_AEC")]
    return _finish(p,"usb_mode",raw,["Ground/power coupling rather than microphone self-noise","USB scheduling rather than acoustic propagation delay","Desk reflection rather than bezel-array mismatch"],"MEASURE_HUM_USB_TIMING_BEZEL_ARRAY_AND_DESK_TRANSFER_ACROSS_DISPLAY_POWER_AND_ORIENTATION_STATES",["Hum and array spread share a declared level reference","USB latency excludes network transport","Desk delay and orientation count are supplied coverage proxies"],["Power/ground topology and USB tail-latency distribution","Frequency-dependent desk/bezel transfer","Physical conference quality and qualified Human acceptance"],{"hum_source_verified":False,"usb_continuity_verified":False,"desk_transfer_verified":False,"physical_monitor_verified":False})


SMART_SCALARS={"woofer_to_mic_coupling_db":(-200.0,200.0),"maximum_woofer_to_mic_coupling_db":(-200.0,200.0),"wakeword_snr_db":(-100.0,200.0),"minimum_wakeword_snr_db":(-100.0,200.0),"array_aliasing_frequency_hz":(1.0,1000000.0),"minimum_array_aliasing_frequency_hz":(1.0,1000000.0),"talker_azimuth_count":(1,1000),"minimum_talker_azimuth_count":(1,1000),"room_mode_spread_db":(0.0,100.0),"maximum_room_mode_spread_db":(0.0,100.0),"aec_tail_ms":(0.0,10000.0),"minimum_aec_tail_ms":(0.0,10000.0)}


def validate_smart_speaker(p):
    expected=set(SMART_SCALARS)|{"model","array_topology","physical_smart_speaker_verified"}
    if not isinstance(p,dict) or set(p)!=expected:raise ValueError("exact smart-speaker far-field budget required")
    if p["model"]!="SUPPLIED_SMART_SPEAKER_FAR_FIELD_SELF_ECHO_BUDGET":raise ValueError("unsupported smart-speaker model")
    if p["array_topology"] not in {"CIRCULAR_ARRAY_DECLARED","PLANAR_ARRAY_DECLARED"}:raise ValueError("unsupported smart-speaker array")
    if p["physical_smart_speaker_verified"] is not False:raise ValueError("physical smart-speaker acceptance requires external Evidence")
    for key,bounds in SMART_SCALARS.items():_number(p[key],*bounds)
    if not isinstance(p["talker_azimuth_count"],int) or not isinstance(p["minimum_talker_azimuth_count"],int):raise ValueError("integer talker coverage required")


def analyze_smart_speaker(p):
    validate_smart_speaker(p)
    raw=[("WOOFER_MIC_COUPLING",p["woofer_to_mic_coupling_db"],p["maximum_woofer_to_mic_coupling_db"],"<=","REVISE_WOOFER_ISOLATION_MIC_LOCATION_OR_AEC_RANGE"),("WAKEWORD_SNR",p["wakeword_snr_db"],p["minimum_wakeword_snr_db"],">=","REVISE_FAR_FIELD_ARRAY_OR_PLAYBACK_COEXISTENCE"),("ARRAY_ALIASING_FREQUENCY",p["array_aliasing_frequency_hz"],p["minimum_array_aliasing_frequency_hz"],">=","REDUCE_ARRAY_SPACING_OR_BOUND_STEERING_BAND"),("TALKER_AZIMUTH_COVERAGE",p["talker_azimuth_count"],p["minimum_talker_azimuth_count"],">=","EXPAND_TALKER_AZIMUTH_AND_DISTANCE_MATRIX"),("ROOM_MODE_SPREAD",p["room_mode_spread_db"],p["maximum_room_mode_spread_db"],"<=","REVISE_PLACEMENT_OR_ROOM_ROBUST_TUNING"),("AEC_TAIL_COVERAGE",p["aec_tail_ms"],p["minimum_aec_tail_ms"],">=","EXTEND_ECHO_TAIL_OR_REDUCE_ROOM_PATH")]
    return _finish(p,"array_topology",raw,["Self-echo nonlinearity rather than NR weakness","Room mode rather than transducer peak","Array aliasing rather than wakeword-model regression"],"MEASURE_PLAYBACK_COUPLING_ARRAY_TRANSFER_WAKEWORD_SNR_AND_ROOM_ECHO_ACROSS_TALKER_AND_PLACEMENT_STATES",["Coupling and wakeword SNR use supplied scalar references","Aliasing frequency is declared from the intended geometry","Room spread and AEC tail are coverage proxies"],["Nonlinear self-echo and actual wakeword corpus performance","Continuous 3D array response and room distribution","Physical smart-speaker and qualified Human acceptance"],{"wakeword_quality_verified":False,"array_calibration_verified":False,"aec_verified":False,"physical_smart_speaker_verified":False})


def _finish(p,label,raw,counters,experiment,assumptions,unresolved,claims):
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {label:p[label],"checks":checks,"required_revisions":[c["on_failure"] for c in checks if not c["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(c["passed"] for c in checks) else "DESIGN_REVISION_REQUIRED",**claims,"physical_measurement_verified":False,"counter_hypotheses":counters,"next_discriminating_experiment":experiment,"model_assumptions":assumptions,"unresolved":unresolved}
