"""Independent R069 review of the bounded R045 hearing-aid decision."""
from __future__ import annotations

import math


def _same(actual,expected):
    if isinstance(expected,dict): return isinstance(actual,dict) and set(actual)==set(expected) and all(_same(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list): return isinstance(actual,list) and len(actual)==len(expected) and all(_same(a,e) for a,e in zip(actual,expected))
    if isinstance(expected,bool) or expected is None: return actual is expected
    if isinstance(expected,(int,float)): return isinstance(actual,(int,float)) and not isinstance(actual,bool) and math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-12)
    return actual==expected


def review(parameters,candidate):
    from .hearing_aid_product import validate,_values
    validate(parameters)
    if not isinstance(candidate,dict): raise ValueError("hearing-aid candidate object required")
    p=parameters;effective_gain,gain_margin,feedback_margin,predicted_output,receiver_headroom=_values(p)
    raw=[
        ("PRESCRIBED_GAIN",gain_margin,p["minimum_gain_margin_db"],">=","REASSESS_VENT_RECEIVER_AND_GAIN_BEFORE_ANY_FITTING_CLAIM"),
        ("FEEDBACK_MARGIN",feedback_margin,p["minimum_feedback_margin_db"],">=","REDUCE_GAIN_OR_REVISE_FEEDBACK_PATH_WITH_REAL_EAR_RETEST"),
        ("PREDICTED_OUTPUT",predicted_output,p["maximum_allowed_output_spl_db"],"<=","LOWER_GAIN_OR_OUTPUT_LIMIT_BEFORE_USE"),
        ("DEVICE_MPO",p["maximum_power_output_spl_db"],p["maximum_allowed_output_spl_db"],"<=","LOWER_DEVICE_MPO_AND_REQUIRE_QUALIFIED_SAFETY_REVIEW"),
        ("RECEIVER_HEADROOM",receiver_headroom,p["minimum_receiver_headroom_db"],">=","REVISE_RECEIVER_OR_GAIN_BUDGET")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"effective_coupler_gain_db":effective_gain,"conservative_gain_margin_db":gain_margin,
        "feedback_margin_db":feedback_margin,"predicted_output_spl_db":predicted_output,"receiver_headroom_db":receiver_headroom,
        "fitting_context":p["fitting_context"],"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],
        "disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED",
        "clinical_efficacy_verified":False,"clinical_fitting_verified":False,"real_ear_verified":False,"physical_measurement_verified":False,
        "counter_hypotheses":["Vent leakage rather than receiver deficit","Coupler-to-ear transfer rather than algorithm instability","Output limiter setting rather than prescribed-gain shortage"],
        "next_discriminating_experiment":"QUALIFIED_REAL_EAR_GAIN_FEEDBACK_AND_MPO_MEASUREMENT_WITH_PATIENT_SPECIFIC_APPROVAL",
        "model_assumptions":["Coupler gain and vent loss combine as supplied scalar dB terms","Feedback onset is a supplied same-configuration bound","Predicted output is input plus effective linear-region gain"],
        "unresolved":["Individual ear-canal transfer and prescribed fitting rationale","Nonlinear compression and adaptive feedback behavior","Clinical efficacy, calibrated real-ear Evidence and qualified Human approval"]}
    if set(candidate)!=set(expected): raise ValueError("exact hearing-aid assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"hearing-aid-acoustic-boundary","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,
            "observations":{"bounded_scope":"coupler/vent/gain/feedback/MPO arithmetic","unresolved":"patient-specific prescription, real-ear transfer and clinical benefit"},
            "human_approval":False,"role_l3_awarded":False,"scope":"bounded hearing-aid acoustic report consistency only"}


def review_otc(parameters,candidate):
    from .hearing_aid_product import validate_otc,_otc_values
    validate_otc(parameters)
    if not isinstance(candidate,dict): raise ValueError("OTC self-fit candidate object required")
    p=parameters;effective,target_error,predicted=_otc_values(p)
    raw=[
        ("USER_GAIN_CONTROL",p["user_gain_setting_db"],p["maximum_user_gain_db"],"<=","CAP_USER_GAIN_CONTROL"),
        ("SELF_FIT_TARGET_ERROR",target_error,p["maximum_target_error_db"],"<=","REPEAT_SELF_FIT_WITH_SEAL_AND_INSTRUCTION_CHECK"),
        ("PREDICTED_OUTPUT",predicted,p["maximum_allowed_output_spl_db"],"<=","LOWER_USER_GAIN_OR_INPUT_LEVEL"),
        ("OUTPUT_LIMITER",p["output_limiter_spl_db"],p["maximum_allowed_output_spl_db"],"<=","LOWER_LIMITER_AND_REQUIRE_PRODUCT_SAFETY_REVIEW"),
        ("INSTRUCTION_COMPREHENSION",p["instruction_comprehension_fraction"],p["minimum_instruction_comprehension_fraction"],">=","REVISE_GUIDANCE_AND_REPEAT_ACCESSIBILITY_STUDY"),
        ("SEAL_REPEATABILITY",p["seal_repeatability_spread_db"],p["maximum_seal_spread_db"],"<=","REVISE_FIT_INTERFACE_BEFORE_GAIN_INCREASE")]
    rows=[{"id":i,"actual":a,"limit":l,"operator":o,"passed":a<=l if o=="<=" else a>=l,"on_failure":f} for i,a,l,o,f in raw]
    expected={"effective_self_fit_gain_db":effective,"self_fit_target_error_db":target_error,"predicted_output_spl_db":predicted,
        "self_fit_mode":p["self_fit_mode"],"checks":rows,"required_revisions":[r["on_failure"] for r in rows if not r["passed"]],
        "disposition":"BOUNDED_BASELINE_ACCEPT" if all(r["passed"] for r in rows) else "DESIGN_REVISION_REQUIRED",
        "clinical_indication_verified":False,"usability_verified":False,"physical_user_study_verified":False,"physical_measurement_verified":False,
        "counter_hypotheses":["Seal loss rather than insufficient user gain","Instruction failure rather than algorithm defect","Input programme level rather than limiter malfunction"],
        "next_discriminating_experiment":"QUALIFIED_OUTPUT_EXPOSURE_AND_ACCESSIBLE_SELF_FIT_STUDY_ACROSS_REAL_USERS",
        "model_assumptions":["User gain and vent loss combine as scalar dB terms","Programme output remains in a supplied linear budget","Comprehension and fit spread are supplied study-plan values, not observations"],
        "unresolved":["Real-user fit distribution and comprehension","Exposure dose and nonlinear limiter behavior","Clinical indication, physical user study and qualified Human approval"]}
    if set(candidate)!=set(expected): raise ValueError("exact OTC self-fit assertions required")
    differences=[{"field":k,"asserted":candidate[k],"expected":v} for k,v in expected.items() if not _same(candidate[k],v)]
    return {"domain":"otc-self-fit-output-claims","decision":"CHANGES_REQUIRED" if differences else "BOUNDED_REVIEW_ACCEPT","disagreements":differences,
            "observations":{"bounded_scope":"user gain, seal, output, instruction and fit-spread arithmetic","unresolved":"real-user accessibility, exposure and clinical indication"},
            "human_approval":False,"role_l3_awarded":False,"scope":"bounded OTC self-fit report consistency only"}
