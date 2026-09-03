"""Role-specific engineering decisions, separate from shared Skill Goldens."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from ..config import ROOT

TWS_FIELDS={
    'leak_pole_hz':(0,20000),'bass_reference_hz':(1,20000),'max_leak_loss_db':(0,40),
    'feedback_crossover_hz':(1,4000),'feedback_delay_ms':(0,10),'plant_phase_lag_deg':(0,180),
    'min_phase_margin_deg':(1,120),'ff_wind_rms_pa':(0,100),'max_ff_wind_rms_pa':(1e-12,100),
    'call_speech_rms_pa':(1e-12,100),'call_ambient_rms_pa':(1e-12,100),'min_call_snr_db':(-40,100),
    'driver_peak_excursion_mm':(0,10),'safe_peak_excursion_mm':(1e-6,10),
    'occlusion_boost_db':(0,40),'max_occlusion_boost_db':(0,40),
}


def _canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')


def _fingerprint():
    paths=[Path(__file__),ROOT/'aeris_runtime/engineering/domain_review.py',ROOT/'aeris_runtime/engineering/microphone_domain.py']
    for skill in HANDLERS:
        paths.append(ROOT/f'methods/roles/{skill}.json')
        paths.extend(ROOT/f'skills/{skill}/{name}' for name in ('manifest.json','input.schema.json','output.schema.json','SKILL.md'))
    return hashlib.sha256(_canonical({p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})).hexdigest()


def tws_fit_anc_call(params):
    """Single-pole leakage, single-crossover delay and outward-mic noise model.

Does not estimate in-ear transfer, nonlinear ANC stability, real fit, driver
temperature or perceptual quality. These limitations are preserved in outputs.
"""
    if not isinstance(params,dict) or set(params)!=set(TWS_FIELDS):
        raise ValueError('exact TWS SI-unit field contract required; missing/unknown fields rejected')
    for key,(low,high) in TWS_FIELDS.items():
        value=params[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
            raise ValueError(f'{key}: finite declared-unit value in [{low}, {high}] required')
    p=params
    loss=10*math.log10(1+(p['leak_pole_hz']/p['bass_reference_hz'])**2)
    delay_phase=360*p['feedback_crossover_hz']*p['feedback_delay_ms']/1000
    margin=180-p['plant_phase_lag_deg']-delay_phase
    noise=math.hypot(p['call_ambient_rms_pa'],p['ff_wind_rms_pa'])
    snr=20*math.log10(p['call_speech_rms_pa']/noise)
    checks=[]
    def check(identifier,actual,limit,operator,action):
        passed=actual<=limit if operator=='<=' else actual>=limit
        checks.append({'id':identifier,'actual':actual,'limit':limit,'operator':operator,
                       'margin':limit-actual if operator=='<=' else actual-limit,
                       'passed':passed,'on_failure':action})
    check('SEAL_LEAK_LOSS_DB',loss,p['max_leak_loss_db'],'<=','RECHECK_TIP_SEAL_BEFORE_BASS_EQ')
    check('FEEDBACK_PHASE_MARGIN_DEG',margin,p['min_phase_margin_deg'],'>=','LOWER_CROSSOVER_OR_LATENCY_AND_REMEASURE_LOOP')
    check('OUTWARD_FF_WIND_RMS_PA',p['ff_wind_rms_pa'],p['max_ff_wind_rms_pa'],'<=','DISABLE_OR_LIMIT_WIND_EXPOSED_FEEDFORWARD_PATH')
    check('OUTWARD_CALL_SNR_DB',snr,p['min_call_snr_db'],'>=','REVISE_CALL_CAPTURE_PATH_OR_WIND_SHIELDING')
    check('MINIATURE_DRIVER_EXCURSION_MM',p['driver_peak_excursion_mm'],p['safe_peak_excursion_mm'],'<=','LIMIT_BASS_DRIVE_OR_REVISE_RECEIVER')
    check('OCCLUSION_BOOST_DB',p['occlusion_boost_db'],p['max_occlusion_boost_db'],'<=','REVISE_VENT_OR_SIDETONE_WITH_SEAL_RETEST')
    feedback=checks[1]['passed']; feedforward=checks[2]['passed']
    topology='HYBRID' if feedback and feedforward else 'FB_ONLY' if feedback else 'FF_ONLY' if feedforward else 'PASSIVE'
    return {'leak_loss_db':loss,'delay_phase_lag_deg':delay_phase,'phase_margin_deg':margin,
            'call_snr_db':snr,'anc_topology_candidate':topology,'checks':checks,
            'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'counter_hypotheses':['seal leakage rather than insufficient bass EQ',
                'feedback delay rather than feedforward filter magnitude','outward-mic wind rather than stationary ambient noise'],
            'unresolved':['actual ear-fit distribution and inward/outward transfer functions',
                'full-loop multiple-crossover stability, nonlinearities and driver thermal behavior',
                'real call intelligibility, calibration and Human acceptance'],
            'model_assumptions':['single-pole leak attenuation relative to sealed reference',
                'single unity-gain feedback crossover with supplied plant lag and pure delay',
                'outward FF mic reused for call capture; wind and ambient noise uncorrelated',
                'excursion and occlusion are supplied estimates, not newly measured values']}


def speaker_power_distortion(params):
    schema=json.loads((ROOT/'skills/speaker-power-distortion-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact speaker power SI-unit field contract required')
    for key,rules in schema['properties'].items():
        value=params[key]
        if rules['type']=='array':
            if not isinstance(value,list) or not rules['minItems']<=len(value)<=rules['maxItems']:
                raise ValueError('bounded harmonic RMS vector required')
            values=value; rules=rules['items']
        else: values=[value]
        for number in values:
            if (isinstance(number,bool) or not isinstance(number,(float,int)) or not math.isfinite(number)
                    or number<rules.get('minimum',-math.inf) or number>rules.get('maximum',math.inf)
                    or number<=rules.get('exclusiveMinimum',-math.inf)):
                raise ValueError('invalid declared-unit value: '+key)
    p=params
    if p['drive_voltage_rms_v']<p['reference_voltage_rms_v']:
        raise ValueError('power validation requires drive at or above the reference voltage')
    if p['max_coil_temperature_c']<p['ambient_temperature_c']:
        raise ValueError('coil limit is below initial ambient temperature')
    thd=100*math.hypot(*p['harmonic_rms_pa'])/p['fundamental_rms_pa']
    compression=20*math.log10(p['drive_voltage_rms_v']/p['reference_voltage_rms_v'])-20*math.log10(p['fundamental_rms_pa']/p['reference_fundamental_rms_pa'])
    temperature=p['ambient_temperature_c']-p['input_power_w']*p['thermal_resistance_k_per_w']*math.expm1(-p['duration_s']/(p['thermal_resistance_k_per_w']*p['thermal_capacity_j_per_k']))
    checks=[]
    for identifier,actual,limit,revision in (
        ('THD_PERCENT',thd,p['max_thd_percent'],'LOWER_DRIVE_AND_DISCRIMINATE_TRANSDUCER_FROM_AMPLIFIER_NONLINEARITY'),
        ('COMPRESSION_DB',compression,p['max_compression_db'],'SEPARATE_THERMAL_COMPRESSION_FROM_LIMITER_GAIN'),
        ('COIL_TEMPERATURE_C',temperature,p['max_coil_temperature_c'],'REDUCE_DUTY_AND_RECHECK_COIL_TEMPERATURE')):
        checks.append({'id':identifier,'actual':actual,'limit':limit,'margin':limit-actual,'operator':'<=',
                       'passed':actual<=limit,'on_failure':revision})
    compressed=not checks[1]['passed']; hot=not checks[2]['passed']
    experiment=('Measure resistance-derived coil temperature and repeat the level sweep after cooling at identical gain' if compressed and hot else
                'Record amplifier output and limiter gain at matched cold-coil conditions before attributing loss to heat' if compressed else
                'Measure harmonic order trends with verified amplifier headroom and matched acoustic fixture')
    return {'thd_percent':thd,'compression_db':compression,'predicted_coil_temperature_c':temperature,
            'checks':checks,'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'counter_hypotheses':['amplifier clipping rather than transducer nonlinearity',
                'limiter gain reduction rather than thermal compression','fixture response change rather than power compression'],
            'next_discriminating_experiment':experiment,
            'model_assumptions':['same frequency, fixture and harmonic bandwidth','constant real electrical power',
                'single thermal RC starting at ambient; no resistance/temperature feedback'],
            'unresolved':['actual coil temperature and calibration','excursion and nonlinear parameter measurements',
                          'physical reliability, lifetime and qualified Human acceptance']}


from .microphone_domain import analyze as microphone_measurement

HANDLERS={'tws-fit-anc-call-baseline':tws_fit_anc_call,'speaker-power-distortion-baseline':speaker_power_distortion,
          'microphone-reference-noise-headroom-baseline':microphone_measurement}


def _review_handler(domain):
    def run(params):
        from .domain_review import review
        return review(domain,params)
    return run


for _domain in ('speaker-nonlinear','speaker-thermal','tws-anc','tws-fit-capture'):
    HANDLERS[_domain+'-domain-review']=_review_handler(_domain)


def execute(skill_id,params):
    if _fingerprint()!=LOADED_SHA256: raise RuntimeError('Role method source changed after load; restart required')
    if skill_id not in HANDLERS: raise KeyError(skill_id)
    values=HANDLERS[skill_id](params)
    _canonical(values)  # Nonfinite calculation results must never leave as PASS.
    return {'skill_id':skill_id,'version':'1.0.0','result':'PASS','values':values,
            'input_sha256':hashlib.sha256(_canonical(params)).hexdigest(),'implementation_sha256':LOADED_SHA256,
            'capability_maturity':'FREE_LOCAL_BASELINE','evidence_class':'DETERMINISTIC_ROLE_DOMAIN_CALCULATION',
            'uncertainty':'Supplied model parameters and limits are uncalibrated unless separately evidenced; see model assumptions.',
            'physical_measurement_verified':False,'professional_tool_verified':False,
            'truth':'Calculation completion is not role L3, physical acceptance, or product certification.'}


LOADED_SHA256=_fingerprint()
