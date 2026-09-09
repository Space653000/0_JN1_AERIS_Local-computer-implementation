"""Bounded R045 hearing-aid acoustic gain, feedback and output screening."""
from __future__ import annotations

import math


SCALARS={
    "prescribed_insertion_gain_db":(0.0,100.0),"coupler_gain_db":(0.0,100.0),
    "vent_leak_loss_db":(0.0,60.0),"gain_tolerance_db":(0.0,30.0),
    "minimum_gain_margin_db":(0.0,30.0),"feedback_onset_gain_db":(0.0,120.0),
    "minimum_feedback_margin_db":(0.0,60.0),"input_spl_db":(0.0,160.0),
    "maximum_power_output_spl_db":(0.0,180.0),"maximum_allowed_output_spl_db":(0.0,180.0),
    "receiver_output_limit_spl_db":(0.0,180.0),"minimum_receiver_headroom_db":(0.0,30.0),
}


def _number(value,low,high):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError("finite declared hearing-aid value outside bounded applicability")


def validate(parameters):
    expected=set(SCALARS)|{"model","fitting_context","clinical_fitting_claimed","real_ear_verified"}
    if not isinstance(parameters,dict) or set(parameters)!=expected:
        raise ValueError("exact supplied hearing-aid acoustic budget required")
    if parameters["model"]!="SUPPLIED_HEARING_AID_ACOUSTIC_BUDGET": raise ValueError("unsupported hearing-aid model")
    if parameters["fitting_context"] not in {"COUPLER_BASELINE","SYNTHETIC_EAR_CANAL"}: raise ValueError("unsupported fitting context")
    if parameters["clinical_fitting_claimed"] is not False or parameters["real_ear_verified"] is not False:
        raise ValueError("clinical fitting and real-ear verification require external qualified Evidence")
    for key,bounds in SCALARS.items(): _number(parameters[key],*bounds)


def _values(p):
    effective_gain=p["coupler_gain_db"]-p["vent_leak_loss_db"]
    gain_margin=effective_gain-p["gain_tolerance_db"]-p["prescribed_insertion_gain_db"]
    feedback_margin=p["feedback_onset_gain_db"]-p["coupler_gain_db"]
    predicted_output=p["input_spl_db"]+effective_gain
    receiver_headroom=p["receiver_output_limit_spl_db"]-predicted_output
    return effective_gain,gain_margin,feedback_margin,predicted_output,receiver_headroom


def analyze(parameters):
    validate(parameters);p=parameters
    effective_gain,gain_margin,feedback_margin,predicted_output,receiver_headroom=_values(p)
    raw=[
        ("PRESCRIBED_GAIN",gain_margin,p["minimum_gain_margin_db"],">=","REASSESS_VENT_RECEIVER_AND_GAIN_BEFORE_ANY_FITTING_CLAIM"),
        ("FEEDBACK_MARGIN",feedback_margin,p["minimum_feedback_margin_db"],">=","REDUCE_GAIN_OR_REVISE_FEEDBACK_PATH_WITH_REAL_EAR_RETEST"),
        ("PREDICTED_OUTPUT",predicted_output,p["maximum_allowed_output_spl_db"],"<=","LOWER_GAIN_OR_OUTPUT_LIMIT_BEFORE_USE"),
        ("DEVICE_MPO",p["maximum_power_output_spl_db"],p["maximum_allowed_output_spl_db"],"<=","LOWER_DEVICE_MPO_AND_REQUIRE_QUALIFIED_SAFETY_REVIEW"),
        ("RECEIVER_HEADROOM",receiver_headroom,p["minimum_receiver_headroom_db"],">=","REVISE_RECEIVER_OR_GAIN_BUDGET"),
    ]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"effective_coupler_gain_db":effective_gain,"conservative_gain_margin_db":gain_margin,
            "feedback_margin_db":feedback_margin,"predicted_output_spl_db":predicted_output,
            "receiver_headroom_db":receiver_headroom,"fitting_context":p["fitting_context"],"checks":checks,
            "required_revisions":[row["on_failure"] for row in checks if not row["passed"]],
            "disposition":"BOUNDED_BASELINE_ACCEPT" if all(row["passed"] for row in checks) else "DESIGN_REVISION_REQUIRED",
            "clinical_efficacy_verified":False,"clinical_fitting_verified":False,"real_ear_verified":False,
            "physical_measurement_verified":False,
            "counter_hypotheses":["Vent leakage rather than receiver deficit","Coupler-to-ear transfer rather than algorithm instability","Output limiter setting rather than prescribed-gain shortage"],
            "next_discriminating_experiment":"QUALIFIED_REAL_EAR_GAIN_FEEDBACK_AND_MPO_MEASUREMENT_WITH_PATIENT_SPECIFIC_APPROVAL",
            "model_assumptions":["Coupler gain and vent loss combine as supplied scalar dB terms","Feedback onset is a supplied same-configuration bound","Predicted output is input plus effective linear-region gain"],
            "unresolved":["Individual ear-canal transfer and prescribed fitting rationale","Nonlinear compression and adaptive feedback behavior","Clinical efficacy, calibrated real-ear Evidence and qualified Human approval"]}


OTC_SCALARS={
    "user_gain_setting_db":(0.0,80.0),"maximum_user_gain_db":(0.0,80.0),"vent_loss_db":(0.0,60.0),
    "self_fit_target_gain_db":(0.0,80.0),"maximum_target_error_db":(0.0,30.0),"input_spl_db":(0.0,160.0),
    "output_limiter_spl_db":(0.0,180.0),"maximum_allowed_output_spl_db":(0.0,180.0),
    "instruction_comprehension_fraction":(0.0,1.0),"minimum_instruction_comprehension_fraction":(0.0,1.0),
    "seal_repeatability_spread_db":(0.0,60.0),"maximum_seal_spread_db":(0.0,60.0),
}


def validate_otc(parameters):
    expected=set(OTC_SCALARS)|{"model","self_fit_mode","clinical_indication_claimed","physical_user_study_verified"}
    if not isinstance(parameters,dict) or set(parameters)!=expected: raise ValueError("exact OTC self-fit acoustic budget required")
    if parameters["model"]!="SUPPLIED_OTC_SELF_FIT_OUTPUT_BUDGET": raise ValueError("unsupported OTC model")
    if parameters["self_fit_mode"] not in {"GUIDED_APP","DEVICE_CONTROLS"}: raise ValueError("unsupported self-fit mode")
    if parameters["clinical_indication_claimed"] is not False or parameters["physical_user_study_verified"] is not False:
        raise ValueError("clinical indication and user-study verification require external qualified Evidence")
    for key,bounds in OTC_SCALARS.items(): _number(parameters[key],*bounds)


def _otc_values(p):
    effective=p["user_gain_setting_db"]-p["vent_loss_db"]
    target_error=abs(effective-p["self_fit_target_gain_db"])
    predicted=p["input_spl_db"]+effective
    return effective,target_error,predicted


def analyze_otc(parameters):
    validate_otc(parameters);p=parameters;effective,target_error,predicted=_otc_values(p)
    raw=[
        ("USER_GAIN_CONTROL",p["user_gain_setting_db"],p["maximum_user_gain_db"],"<=","CAP_USER_GAIN_CONTROL"),
        ("SELF_FIT_TARGET_ERROR",target_error,p["maximum_target_error_db"],"<=","REPEAT_SELF_FIT_WITH_SEAL_AND_INSTRUCTION_CHECK"),
        ("PREDICTED_OUTPUT",predicted,p["maximum_allowed_output_spl_db"],"<=","LOWER_USER_GAIN_OR_INPUT_LEVEL"),
        ("OUTPUT_LIMITER",p["output_limiter_spl_db"],p["maximum_allowed_output_spl_db"],"<=","LOWER_LIMITER_AND_REQUIRE_PRODUCT_SAFETY_REVIEW"),
        ("INSTRUCTION_COMPREHENSION",p["instruction_comprehension_fraction"],p["minimum_instruction_comprehension_fraction"],">=","REVISE_GUIDANCE_AND_REPEAT_ACCESSIBILITY_STUDY"),
        ("SEAL_REPEATABILITY",p["seal_repeatability_spread_db"],p["maximum_seal_spread_db"],"<=","REVISE_FIT_INTERFACE_BEFORE_GAIN_INCREASE")]
    checks=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    return {"effective_self_fit_gain_db":effective,"self_fit_target_error_db":target_error,"predicted_output_spl_db":predicted,
            "self_fit_mode":p["self_fit_mode"],"checks":checks,"required_revisions":[r["on_failure"] for r in checks if not r["passed"]],
            "disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in checks) else "DESIGN_REVISION_REQUIRED",
            "clinical_indication_verified":False,"usability_verified":False,"physical_user_study_verified":False,"physical_measurement_verified":False,
            "counter_hypotheses":["Seal loss rather than insufficient user gain","Instruction failure rather than algorithm defect","Input programme level rather than limiter malfunction"],
            "next_discriminating_experiment":"QUALIFIED_OUTPUT_EXPOSURE_AND_ACCESSIBLE_SELF_FIT_STUDY_ACROSS_REAL_USERS",
            "model_assumptions":["User gain and vent loss combine as scalar dB terms","Programme output remains in a supplied linear budget","Comprehension and fit spread are supplied study-plan values, not observations"],
            "unresolved":["Real-user fit distribution and comprehension","Exposure dose and nonlinear limiter behavior","Clinical indication, physical user study and qualified Human approval"]}
