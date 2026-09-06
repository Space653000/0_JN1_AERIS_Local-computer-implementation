"""Independent exact-output reviewers for conference product budgets."""
from __future__ import annotations

import math


def _same(actual,expected):
    if isinstance(expected,dict):return isinstance(actual,dict) and set(actual)==set(expected) and all(_same(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):return isinstance(actual,list) and len(actual)==len(expected) and all(_same(a,e) for a,e in zip(actual,expected))
    if isinstance(expected,bool) or expected is None:return actual is expected
    if isinstance(expected,(int,float)):return isinstance(actual,(int,float)) and not isinstance(actual,bool) and math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-12)
    return actual==expected


def review_monitor(p,candidate):
    from .conference_products import validate_monitor
    validate_monitor(p)
    raw=[("POWER_SUPPLY_HUM",p["power_supply_hum_db"],p["maximum_power_supply_hum_db"],"<=","ISOLATE_GROUND_OR_POWER_COUPLING_BEFORE_DIGITAL_NOTCH"),("BEZEL_ARRAY_SPREAD",p["bezel_array_spread_db"],p["maximum_bezel_array_spread_db"],"<=","REVISE_BEZEL_PORT_OR_ARRAY_EQUALIZATION"),("DESK_REFLECTION_DELAY",p["desk_reflection_delay_ms"],p["minimum_desk_reflection_delay_ms"],">=","REVISE_DESK_DISTANCE_OR_REFLECTION_GATING"),("USB_AUDIO_LATENCY",p["usb_audio_latency_ms"],p["maximum_usb_audio_latency_ms"],"<=","REVISE_USB_BUFFER_SCHEDULING_OR_CLOCK_POLICY"),("DISPLAY_ORIENTATION_COVERAGE",p["display_orientation_count"],p["minimum_display_orientation_count"],">=","EXPAND_DISPLAY_TILT_HEIGHT_AND_DESK_MATRIX"),("ECHO_REFERENCE_ALIGNMENT",p["echo_reference_alignment_ms"],p["maximum_echo_reference_alignment_ms"],"<=","ALIGN_USB_PLAYBACK_REFERENCE_BEFORE_AEC")]
    expected=_expected(p,"usb_mode",raw,["Ground/power coupling rather than microphone self-noise","USB scheduling rather than acoustic propagation delay","Desk reflection rather than bezel-array mismatch"],"MEASURE_HUM_USB_TIMING_BEZEL_ARRAY_AND_DESK_TRANSFER_ACROSS_DISPLAY_POWER_AND_ORIENTATION_STATES",["Hum and array spread share a declared level reference","USB latency excludes network transport","Desk delay and orientation count are supplied coverage proxies"],["Power/ground topology and USB tail-latency distribution","Frequency-dependent desk/bezel transfer","Physical conference quality and qualified Human acceptance"],{"hum_source_verified":False,"usb_continuity_verified":False,"desk_transfer_verified":False,"physical_monitor_verified":False})
    return _finish("monitor-aio-usb-desk",candidate,expected,"hum/bezel/desk/USB/orientation/echo-reference")


def review_smart_speaker(p,candidate):
    from .conference_products import validate_smart_speaker
    validate_smart_speaker(p)
    raw=[("WOOFER_MIC_COUPLING",p["woofer_to_mic_coupling_db"],p["maximum_woofer_to_mic_coupling_db"],"<=","REVISE_WOOFER_ISOLATION_MIC_LOCATION_OR_AEC_RANGE"),("WAKEWORD_SNR",p["wakeword_snr_db"],p["minimum_wakeword_snr_db"],">=","REVISE_FAR_FIELD_ARRAY_OR_PLAYBACK_COEXISTENCE"),("ARRAY_ALIASING_FREQUENCY",p["array_aliasing_frequency_hz"],p["minimum_array_aliasing_frequency_hz"],">=","REDUCE_ARRAY_SPACING_OR_BOUND_STEERING_BAND"),("TALKER_AZIMUTH_COVERAGE",p["talker_azimuth_count"],p["minimum_talker_azimuth_count"],">=","EXPAND_TALKER_AZIMUTH_AND_DISTANCE_MATRIX"),("ROOM_MODE_SPREAD",p["room_mode_spread_db"],p["maximum_room_mode_spread_db"],"<=","REVISE_PLACEMENT_OR_ROOM_ROBUST_TUNING"),("AEC_TAIL_COVERAGE",p["aec_tail_ms"],p["minimum_aec_tail_ms"],">=","EXTEND_ECHO_TAIL_OR_REDUCE_ROOM_PATH")]
    expected=_expected(p,"array_topology",raw,["Self-echo nonlinearity rather than NR weakness","Room mode rather than transducer peak","Array aliasing rather than wakeword-model regression"],"MEASURE_PLAYBACK_COUPLING_ARRAY_TRANSFER_WAKEWORD_SNR_AND_ROOM_ECHO_ACROSS_TALKER_AND_PLACEMENT_STATES",["Coupling and wakeword SNR use supplied scalar references","Aliasing frequency is declared from the intended geometry","Room spread and AEC tail are coverage proxies"],["Nonlinear self-echo and actual wakeword corpus performance","Continuous 3D array response and room distribution","Physical smart-speaker and qualified Human acceptance"],{"wakeword_quality_verified":False,"array_calibration_verified":False,"aec_verified":False,"physical_smart_speaker_verified":False})
    return _finish("smart-speaker-far-field-self-echo",candidate,expected,"coupling/wakeword/aliasing/talker/room/AEC-tail")


def _expected(p,label,raw,counters,experiment,assumptions,unresolved,claims):
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {label:p[label],"checks":checks,"required_revisions":[c["on_failure"] for c in checks if not c["passed"]],"disposition":"BOUNDED_BASELINE_ACCEPT" if all(c["passed"] for c in checks) else "DESIGN_REVISION_REQUIRED",**claims,"physical_measurement_verified":False,"counter_hypotheses":counters,"next_discriminating_experiment":experiment,"model_assumptions":assumptions,"unresolved":unresolved}


def _finish(domain,candidate,expected,scope):
    if not isinstance(candidate,dict) or set(candidate)!=set(expected):raise ValueError("exact conference-product assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":domain,"decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,"observations":{"bounded_scope":scope,"unresolved":"physical product distribution and Human acceptance"},"human_approval":False,"role_l3_awarded":False,"scope":"bounded conference-product report consistency only"}
