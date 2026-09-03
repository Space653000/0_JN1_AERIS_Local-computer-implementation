"""Supplied-reference microphone measurements with identifiable noise bounds."""
from __future__ import annotations

import json
import math

from ..config import ROOT


def analyze(params):
    from .domain_review import _validate
    schema=json.loads((ROOT/'skills/microphone-reference-noise-headroom-baseline/input.schema.json').read_text())
    _validate(params,schema)
    p=params
    if p['minimum_sensitivity_dbv_per_pa']>p['maximum_sensitivity_dbv_per_pa']:
        raise ValueError('inverted sensitivity requirement')
    if p['calibrator_output_rms_v']*math.sqrt(2)>=p['adc_peak_v']:
        raise ValueError('calibration sine reaches ADC clipping; sensitivity reference invalid')
    if p['frontend_noise_rms_v']>p['total_noise_rms_v']:
        raise ValueError('frontend noise exceeds total in the declared common output frame')
    sensitivity=p['calibrator_output_rms_v']/p['calibration_gain_linear']/p['calibrator_pressure_rms_pa']
    sensitivity_db=20*math.log10(sensitivity)
    pressure_bound=p['pressure_relative_bound']; gain_bound=p['gain_relative_bound']; noise_bound=p['noise_relative_bound']
    sensitivity_low=sensitivity/(1+pressure_bound)/(1+gain_bound)
    sensitivity_high=sensitivity/(1-pressure_bound)/(1-gain_bound)
    chain=p['analysis_gain_linear']*sensitivity
    chain_low=p['analysis_gain_linear']*(1-gain_bound)*sensitivity_low
    chain_high=p['analysis_gain_linear']*(1+gain_bound)*sensitivity_high
    total=p['total_noise_rms_v']; frontend=p['frontend_noise_rms_v']; ambient=p['ambient_noise_rms_pa']
    variance=(total*total-frontend*frontend)/(chain*chain)-ambient*ambient
    low_variance=((total*(1-noise_bound))**2-(frontend*(1+noise_bound))**2)/(chain_high**2)-(ambient*(1+noise_bound))**2
    high_variance=((total*(1+noise_bound))**2-(frontend*(1-noise_bound))**2)/(chain_low**2)-(ambient*(1-noise_bound))**2
    # Subtraction near a dominant floor is not an intrinsic-noise measurement.
    resolved=variance>max(1e-30,(total/chain)**2*1e-12) and low_variance>0
    noise_pa=math.sqrt(variance) if resolved else None
    noise_db=20*math.log10(noise_pa/20e-6) if resolved else None
    noise_upper=20*math.log10(math.sqrt(high_variance)/20e-6) if high_variance>0 else None
    required_pressure=20e-6*10**(p['required_spl_db']/20)
    peak=chain*required_pressure*p['signal_crest_factor']
    peak_upper=chain_high*required_pressure*p['signal_crest_factor']
    headroom=20*math.log10(p['adc_peak_v']/peak)
    headroom_low=20*math.log10(p['adc_peak_v']/peak_upper)
    sensitivity_interval=[20*math.log10(sensitivity_low),20*math.log10(sensitivity_high)]
    checks=[
        {'id':'SENSITIVITY_INTERVAL','passed':sensitivity_interval[0]>=p['minimum_sensitivity_dbv_per_pa'] and sensitivity_interval[1]<=p['maximum_sensitivity_dbv_per_pa'],
         'on_failure':'RECHECK_PRESSURE_GAIN_AND_REFERENCE_COUPLING'},
        {'id':'IDENTIFIABLE_SELF_NOISE','passed':resolved,'on_failure':'SEPARATE_ROOM_AND_FRONTEND_NOISE_BEFORE_CAPSULE_ATTRIBUTION'},
        {'id':'SELF_NOISE_UPPER_BOUND','passed':resolved and noise_upper<=p['maximum_self_noise_spl_db'],'on_failure':'REDUCE_INPUT_NOISE_AND_REPEAT_COMMON_BANDWIDTH_RUN'},
        {'id':'ELECTRICAL_HEADROOM','passed':headroom_low>=p['minimum_electrical_headroom_db'],'on_failure':'REDUCE_DEPLOYMENT_GAIN_OR_REVISE_ADC_RANGE'},
    ]
    experiment=('QUIETER_ROOM_OR_CALIBRATOR_COUPLING' if ambient>=frontend/chain else 'LOWER_NOISE_FRONTEND_AT_MATCHED_GAIN') if not resolved else 'LEVEL_SWEEP_WITH_DISTORTION_BEFORE_ANY_CAPSULE_OVERLOAD_CLAIM'
    return {'sensitivity_dbv_per_pa':sensitivity_db,'sensitivity_interval_dbv_per_pa':sensitivity_interval,
            'self_noise_rms_pa':noise_pa,'self_noise_spl_db':noise_db,'self_noise_upper_spl_db':noise_upper,
            'noise_resolved':resolved,'electrical_headroom_db':headroom,'electrical_headroom_lower_db':headroom_low,
            'predicted_output_peak_v':peak,'checks':checks,
            'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'counter_hypotheses':['room noise rather than capsule self-noise','frontend noise rather than capsule noise',
                'calibrator coupling or gain-reference error rather than capsule sensitivity drift'],
            'next_discriminating_experiment':experiment,'capsule_overload_verified':False,
            'model_assumptions':['common-bandwidth uncorrelated RMS noise sources','supplied sinusoidal calibration reference',
                'conservative independent relative bounds, not a statistical confidence interval'],
            'unresolved':['actual acoustic calibration and instrument uncertainty','correlated noise and capsule acoustic overload',
                'physical microphone measurement and qualified Human acceptance']}
