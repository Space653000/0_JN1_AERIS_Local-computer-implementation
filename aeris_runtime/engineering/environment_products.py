"""Bounded product decisions for display, outdoor, appliance and open-ear audio."""
from __future__ import annotations
import math


def _number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("finite supplied product scalar outside bounded applicability")


def _validate(parameters, scalars, fixed, model, claim):
    expected = set(scalars) | set(fixed) | {"model", claim}
    if not isinstance(parameters, dict) or set(parameters) != expected:
        raise ValueError("exact product decision budget required")
    if parameters["model"] != model:
        raise ValueError("unsupported product decision model")
    if parameters[claim] is not False:
        raise ValueError("physical product acceptance requires external Evidence")
    for key, bounds in scalars.items():
        _number(parameters[key], *bounds)


def _finish(label, raw, counters, experiment, assumptions, unresolved, claims):
    checks = [{"id": i, "actual": a, "limit": l, "operator": o,
               "passed": a <= l if o == "<=" else a >= l, "on_failure": f}
              for i, a, l, o, f in raw]
    return {"architecture": label, "checks": checks,
            "required_revisions": [c["on_failure"] for c in checks if not c["passed"]],
            "disposition": "BOUNDED_BASELINE_ACCEPT" if all(c["passed"] for c in checks) else "DESIGN_REVISION_REQUIRED",
            **claims, "physical_measurement_verified": False,
            "counter_hypotheses": counters, "next_discriminating_experiment": experiment,
            "model_assumptions": assumptions, "unresolved": unresolved}


TV = {"panel_resonance_margin_db": (-100.0, 200.0), "minimum_panel_resonance_margin_db": (-100.0, 200.0),
      "dialogue_headroom_db": (-100.0, 200.0), "minimum_dialogue_headroom_db": (-100.0, 200.0),
      "wall_clearance_mm": (0.0, 10000.0), "minimum_wall_clearance_mm": (0.0, 10000.0),
      "woofer_excursion_mm": (0.0, 100.0), "safe_woofer_excursion_mm": (0.001, 100.0),
      "mount_buzz_level_db": (-200.0, 200.0), "maximum_mount_buzz_level_db": (-200.0, 200.0),
      "placement_count": (1, 1000), "minimum_placement_count": (1, 1000)}


def validate_tv(p):
    _validate(p, TV, {"panel_mount"}, "SUPPLIED_THIN_TV_PANEL_WALL_DIALOGUE_BUDGET", "physical_tv_verified")
    if p["panel_mount"] not in {"WALL_DECLARED", "STAND_DECLARED"}:
        raise ValueError("unsupported TV panel mount")
    if not isinstance(p["placement_count"], int) or not isinstance(p["minimum_placement_count"], int):
        raise ValueError("integer TV placement coverage required")


def analyze_tv(p):
    validate_tv(p)
    raw = [("PANEL_RESONANCE_MARGIN", p["panel_resonance_margin_db"], p["minimum_panel_resonance_margin_db"], ">=", "REVISE_PANEL_EXCITATION_MOUNT_OR_DRIVER_LOCATION"),
           ("DIALOGUE_HEADROOM", p["dialogue_headroom_db"], p["minimum_dialogue_headroom_db"], ">=", "REDUCE_DIALOGUE_EQ_OR_REVISE_OUTPUT_CHAIN"),
           ("WALL_CLEARANCE", p["wall_clearance_mm"], p["minimum_wall_clearance_mm"], ">=", "INCREASE_REAR_PORT_OR_RADIATOR_WALL_CLEARANCE"),
           ("WOOFER_EXCURSION", p["woofer_excursion_mm"], p["safe_woofer_excursion_mm"], "<=", "LIMIT_BASS_DRIVE_OR_REVISE_THIN_TV_TRANSDUCER"),
           ("MOUNT_BUZZ_LEVEL", p["mount_buzz_level_db"], p["maximum_mount_buzz_level_db"], "<=", "ISOLATE_STAND_WALL_OR_PANEL_BUZZ_PATH"),
           ("PLACEMENT_COVERAGE", p["placement_count"], p["minimum_placement_count"], ">=", "EXPAND_WALL_AND_STAND_PLACEMENT_MATRIX")]
    return _finish(p["panel_mount"], raw,
                   ["Panel resonance rather than driver breakup", "Mount buzz rather than amplifier distortion", "Wall loading rather than dialogue-EQ defect"],
                   "MEASURE_PANEL_VELOCITY_DRIVER_EXCURSION_DIALOGUE_HEADROOM_AND_BUZZ_OVER_WALL_AND_STAND_PLACEMENTS",
                   ["Margins are supplied scalar summaries", "Wall clearance is a geometry proxy", "Placement count is coverage metadata"],
                   ["Panel modal field and mount transfer", "Frequency-dependent wall loading", "Physical display and listener acceptance"],
                   {"panel_mode_verified": False, "dialogue_quality_verified": False, "physical_tv_verified": False})


DOORBELL = {"wet_mesh_loss_db": (0.0, 100.0), "maximum_wet_mesh_loss_db": (0.0, 100.0),
            "wind_noise_level_db": (-200.0, 200.0), "maximum_wind_noise_level_db": (-200.0, 200.0),
            "intercom_feedback_margin_db": (-100.0, 200.0), "minimum_intercom_feedback_margin_db": (-100.0, 200.0),
            "echo_coupling_db": (-200.0, 200.0), "maximum_echo_coupling_db": (-200.0, 200.0),
            "mount_resonance_level_db": (-200.0, 200.0), "maximum_mount_resonance_level_db": (-200.0, 200.0),
            "weather_state_count": (1, 1000), "minimum_weather_state_count": (1, 1000)}


def validate_doorbell(p):
    _validate(p, DOORBELL, {"weather_set"}, "SUPPLIED_DOORBELL_WEATHER_INTERCOM_BUDGET", "physical_doorbell_verified")
    if p["weather_set"] not in {"DRY_WIND_RAIN_DECLARED", "DRY_AND_RAIN_DECLARED"}:
        raise ValueError("unsupported doorbell weather set")
    if not isinstance(p["weather_state_count"], int) or not isinstance(p["minimum_weather_state_count"], int):
        raise ValueError("integer weather coverage required")


def analyze_doorbell(p):
    validate_doorbell(p)
    raw = [("WET_MESH_LOSS", p["wet_mesh_loss_db"], p["maximum_wet_mesh_loss_db"], "<=", "REVISE_HYDROPHOBIC_MESH_PORT_OR_GAIN_BUDGET"),
           ("WIND_NOISE_LEVEL", p["wind_noise_level_db"], p["maximum_wind_noise_level_db"], "<=", "REVISE_PORT_ORIENTATION_WIND_SHIELD_OR_CAPTURE_POLICY"),
           ("INTERCOM_FEEDBACK_MARGIN", p["intercom_feedback_margin_db"], p["minimum_intercom_feedback_margin_db"], ">=", "REDUCE_LOOP_GAIN_DELAY_OR_REVISE_SPEAKER_MIC_ISOLATION"),
           ("ECHO_COUPLING", p["echo_coupling_db"], p["maximum_echo_coupling_db"], "<=", "REVISE_MOUNT_SPEAKER_MIC_PATH_OR_AEC_RANGE"),
           ("MOUNT_RESONANCE_LEVEL", p["mount_resonance_level_db"], p["maximum_mount_resonance_level_db"], "<=", "ISOLATE_WALL_MOUNT_RESONANCE_BEFORE_CAPTURE_RETUNING"),
           ("WEATHER_STATE_COVERAGE", p["weather_state_count"], p["minimum_weather_state_count"], ">=", "EXPAND_DRY_WIND_RAIN_AND_DRAINAGE_STATE_MATRIX")]
    return _finish(p["weather_set"], raw,
                   ["Water loading rather than capsule failure", "Wall mounting rather than echo-algorithm regression", "Wind direction rather than stationary noise"],
                   "MEASURE_PORT_TRANSFER_WIND_INTERCOM_LOOP_AND_MOUNT_RESPONSE_ACROSS_DECLARED_WEATHER_STATES",
                   ["Weather losses are supplied scalar extrema", "Feedback margin uses one declared loop state", "State count is not a weather population"],
                   ["Dynamic wetting and drainage transfer", "Nonlinear loudspeaker/microphone echo path", "Outdoor product and Human intercom acceptance"],
                   {"weather_transfer_verified": False, "intercom_quality_verified": False, "physical_doorbell_verified": False})


APPLIANCE = {"motor_harmonic_capture_db": (-200.0, 200.0), "maximum_motor_harmonic_capture_db": (-200.0, 200.0),
             "operating_state_count": (1, 1000), "minimum_operating_state_count": (1, 1000),
             "notification_headroom_db": (-100.0, 200.0), "minimum_notification_headroom_db": (-100.0, 200.0),
             "driver_duty_percent": (0.0, 100.0), "maximum_driver_duty_percent": (0.0, 100.0),
             "enclosure_leak_loss_db": (0.0, 100.0), "maximum_enclosure_leak_loss_db": (0.0, 100.0),
             "command_snr_db": (-100.0, 200.0), "minimum_command_snr_db": (-100.0, 200.0)}


def validate_appliance(p):
    _validate(p, APPLIANCE, {"motor_state_set"}, "SUPPLIED_APPLIANCE_MOTOR_NOTIFICATION_VOICE_BUDGET", "physical_appliance_verified")
    if p["motor_state_set"] not in {"OFF_IDLE_NOMINAL_MAXIMUM", "OFF_AND_LOADED_DECLARED"}:
        raise ValueError("unsupported appliance motor-state set")
    if not isinstance(p["operating_state_count"], int) or not isinstance(p["minimum_operating_state_count"], int):
        raise ValueError("integer appliance-state coverage required")


def analyze_appliance(p):
    validate_appliance(p)
    raw = [("MOTOR_HARMONIC_CAPTURE", p["motor_harmonic_capture_db"], p["maximum_motor_harmonic_capture_db"], "<=", "REVISE_MIC_LOCATION_ISOLATION_OR_MOTOR_STATE_PROCESSING"),
           ("OPERATING_STATE_COVERAGE", p["operating_state_count"], p["minimum_operating_state_count"], ">=", "EXPAND_MOTOR_LOAD_AND_DUTY_STATE_MATRIX"),
           ("NOTIFICATION_HEADROOM", p["notification_headroom_db"], p["minimum_notification_headroom_db"], ">=", "REDUCE_TONE_GAIN_OR_REVISE_OUTPUT_CHAIN"),
           ("DRIVER_DUTY", p["driver_duty_percent"], p["maximum_driver_duty_percent"], "<=", "REDUCE_NOTIFICATION_DUTY_OR_REVISE_THERMAL_DESIGN"),
           ("ENCLOSURE_LEAK_LOSS", p["enclosure_leak_loss_db"], p["maximum_enclosure_leak_loss_db"], "<=", "REVISE_GASKET_ENCLOSURE_OR_TUNING_ASSUMPTION"),
           ("COMMAND_SNR", p["command_snr_db"], p["minimum_command_snr_db"], ">=", "REVISE_CAPTURE_PATH_MOTOR_NOISE_POLICY_OR_MIC_ARRAY")]
    return _finish(p["motor_state_set"], raw,
                   ["Motor operating state rather than microphone defect", "Enclosure leak rather than equalization error", "Duty-cycle heating rather than steady output weakness"],
                   "MEASURE_MOTOR_ORDER_CAPTURE_NOTIFICATION_OUTPUT_TEMPERATURE_AND_COMMAND_PERFORMANCE_OVER_LOAD_STATES",
                   ["Motor and leak terms are supplied scalar summaries", "Duty percent is a declared worst-case schedule", "Command SNR is not recognition accuracy"],
                   ["Motor order spectra and structural paths", "Driver thermal history and enclosure distribution", "Physical appliance and command usability acceptance"],
                   {"motor_path_verified": False, "command_quality_verified": False, "physical_appliance_verified": False})


OPEN_EAR = {"audibility_margin_db": (-100.0, 200.0), "minimum_audibility_margin_db": (-100.0, 200.0),
            "privacy_leakage_db": (-200.0, 200.0), "maximum_privacy_leakage_db": (-200.0, 200.0),
            "head_pose_count": (1, 1000), "minimum_head_pose_count": (1, 1000),
            "tracking_latency_ms": (0.0, 1000.0), "maximum_tracking_latency_ms": (0.0, 1000.0),
            "wind_capture_snr_db": (-100.0, 200.0), "minimum_wind_capture_snr_db": (-100.0, 200.0),
            "fit_response_spread_db": (0.0, 100.0), "maximum_fit_response_spread_db": (0.0, 100.0)}


def validate_open_ear(p):
    _validate(p, OPEN_EAR, {"render_path"}, "SUPPLIED_AR_OPEN_EAR_LEAKAGE_TRACKING_WIND_BUDGET", "physical_open_ear_verified")
    if p["render_path"] not in {"OPEN_EAR_STEREO_DECLARED", "OPEN_EAR_ARRAY_DECLARED"}:
        raise ValueError("unsupported open-ear render path")
    if not isinstance(p["head_pose_count"], int) or not isinstance(p["minimum_head_pose_count"], int):
        raise ValueError("integer head-pose coverage required")


def analyze_open_ear(p):
    validate_open_ear(p)
    raw = [("AUDIBILITY_MARGIN", p["audibility_margin_db"], p["minimum_audibility_margin_db"], ">=", "REVISE_OPEN_EAR_OUTPUT_DIRECTIVITY_OR_GAIN"),
           ("PRIVACY_LEAKAGE", p["privacy_leakage_db"], p["maximum_privacy_leakage_db"], "<=", "REDUCE_LEVEL_OR_REVISE_NEAR_EAR_DIRECTIVITY"),
           ("HEAD_POSE_COVERAGE", p["head_pose_count"], p["minimum_head_pose_count"], ">=", "EXPAND_HEAD_POSE_AND_FIT_MATRIX"),
           ("TRACKING_LATENCY", p["tracking_latency_ms"], p["maximum_tracking_latency_ms"], "<=", "ALIGN_IMU_RENDER_AND_AUDIO_TIMESTAMPS"),
           ("WIND_CAPTURE_SNR", p["wind_capture_snr_db"], p["minimum_wind_capture_snr_db"], ">=", "REVISE_PORT_ORIENTATION_WIND_POLICY_OR_CAPTURE_ARRAY"),
           ("FIT_RESPONSE_SPREAD", p["fit_response_spread_db"], p["maximum_fit_response_spread_db"], "<=", "REVISE_TEMPLE_GEOMETRY_DIRECTIVITY_OR_FIT_COMPENSATION")]
    return _finish(p["render_path"], raw,
                   ["Ear geometry rather than driver mismatch", "Wind turbulence rather than digital noise", "Timestamp skew rather than HRTF defect"],
                   "MEASURE_NEAR_EAR_AND_BYSTANDER_TRANSFER_WIND_CAPTURE_AND_HEAD_TRACKING_OVER_POSE_AND_FIT",
                   ["Audibility and leakage use supplied reference levels", "Pose count is coverage metadata", "Tracking latency is a scalar serial budget"],
                   ["Continuous anatomy-dependent transfer and privacy field", "IMU/audio clock covariance", "Physical fit, safety and listener acceptance"],
                   {"privacy_field_verified": False, "head_tracking_verified": False, "physical_open_ear_verified": False})
