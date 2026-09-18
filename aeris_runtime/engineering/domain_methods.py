"""Role-specific engineering decisions, separate from shared Skill Goldens."""
from __future__ import annotations

import cmath
import hashlib
import inspect
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
    paths=[Path(__file__),ROOT/'aeris_runtime/engineering/domain_review.py',ROOT/'aeris_runtime/engineering/microphone_domain.py',
           ROOT/'aeris_runtime/engineering/numerical_policy.py',ROOT/'aeris_runtime/engineering/speaker_fr.py',
           ROOT/'aeris_runtime/engineering/speaker_fr_review.py',ROOT/'aeris_runtime/engineering/array_doa.py',
           ROOT/'aeris_runtime/engineering/array_doa_review.py',ROOT/'aeris_runtime/engineering/faca.py',
           ROOT/'aeris_runtime/engineering/faca_review.py',ROOT/'aeris_runtime/engineering/requirement_trace.py',
           ROOT/'aeris_runtime/engineering/requirement_trace_review.py',ROOT/'aeris_runtime/engineering/standard_metadata.py',
           ROOT/'aeris_runtime/engineering/standard_metadata_review.py',ROOT/'aeris_runtime/engineering/sealed_alignment.py',
           ROOT/'aeris_runtime/engineering/sealed_alignment_review.py',ROOT/'aeris_runtime/engineering/array_beam.py',
           ROOT/'aeris_runtime/engineering/array_beam_review.py',ROOT/'aeris_runtime/engineering/capture_clock.py',
           ROOT/'aeris_runtime/engineering/capture_clock_review.py',ROOT/'aeris_runtime/engineering/ported_alignment.py',
           ROOT/'aeris_runtime/engineering/ported_alignment_review.py',ROOT/'aeris_runtime/engineering/speaker_polar.py',
           ROOT/'aeris_runtime/engineering/speaker_polar_review.py',ROOT/'aeris_runtime/engineering/speaker_tonal.py',
           ROOT/'aeris_runtime/engineering/speaker_tonal_review.py',ROOT/'aeris_runtime/engineering/hearing_aid_product.py',
           ROOT/'aeris_runtime/engineering/hearing_aid_product_review.py']
    paths.extend([ROOT/'aeris_runtime/engineering/auracast_product.py',ROOT/'aeris_runtime/engineering/auracast_product_review.py'])
    paths.extend([ROOT/'aeris_runtime/engineering/overear_anc_product.py',ROOT/'aeris_runtime/engineering/overear_anc_product_review.py'])
    paths.extend([ROOT/'aeris_runtime/engineering/personal_device_products.py',ROOT/'aeris_runtime/engineering/personal_device_products_review.py'])
    paths.extend([ROOT/'aeris_runtime/engineering/conference_products.py',ROOT/'aeris_runtime/engineering/conference_products_review.py'])
    paths.extend([ROOT/'aeris_runtime/engineering/av_products.py',ROOT/'aeris_runtime/engineering/av_products_review.py'])
    paths.extend([ROOT/'aeris_runtime/engineering/environment_products.py',ROOT/'aeris_runtime/engineering/environment_products_review.py'])
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


def porous_material_absorption(params):
    """Delany-Bazley (1970) empirical porous-absorber model: normalized
    frequency parameter -> complex characteristic impedance and propagation
    constant -> rigid-backed surface impedance -> normal-incidence
    absorption coefficient. Surface impedance uses the general lossy
    transmission-line form Zs=Zc*coth(gamma*d) (gamma is fully complex
    here, not purely imaginary) -- the simpler -j*Zc*cot(kd) textbook form
    only holds for a lossless line and silently produces a negative-real
    (unphysical) surface impedance if used here; verified against this
    exact failure mode while building this skill.

    The empirical fit is itself only published as valid for
    0.01<=X<=1.0, and even inside that range can still return an
    absorption coefficient outside [0,1] for thin/low-frequency
    combinations (a known model limitation, not a bug) -- both boundaries
    are surfaced as an honest disposition rather than clamped."""
    schema=json.loads((ROOT/'skills/porous-material-absorption-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact porous-material absorption SI-unit field contract required')
    for key,rules in schema['properties'].items():
        value=params[key]
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):
            raise ValueError('finite numeric value required: '+key)
        if value<rules.get('minimum',-math.inf) or value>rules.get('maximum',math.inf) or value<=rules.get('exclusiveMinimum',-math.inf):
            raise ValueError('invalid declared-unit value: '+key)
    p=params
    X=p['air_density_kg_m3']*p['frequency_hz']/p['flow_resistivity_pa_s_m2']
    z0=p['air_density_kg_m3']*p['sound_speed_m_s']
    zc=z0*(1+0.0571*X**-0.754-1j*0.087*X**-0.732)
    omega=2*math.pi*p['frequency_hz']
    gamma=(omega/p['sound_speed_m_s'])*(0.0978*X**-0.700+1j*(1+0.189*X**-0.595))
    zs=zc/cmath.tanh(gamma*p['thickness_m'])
    reflection=(zs-z0)/(zs+z0)
    alpha=1-abs(reflection)**2
    applicable=0.01<=X<=1.0
    physical=0.0<=alpha<=1.0
    target_met=applicable and physical and alpha>=p['minimum_target_absorption']
    check={'id':'ABSORPTION_COEFFICIENT','actual':alpha,'limit':p['minimum_target_absorption'],
           'margin':alpha-p['minimum_target_absorption'],'operator':'>=','passed':bool(target_met),
           'on_failure':'INCREASE_THICKNESS_OR_LOWER_FLOW_RESISTIVITY'}
    if not applicable:
        disposition='MODEL_OUTSIDE_VALIDATED_RANGE'
        required_revisions=['SELECT_MATERIAL_OR_FREQUENCY_WITHIN_DELANY_BAZLEY_X_RANGE_0P01_TO_1P0']
        experiment='Re-measure flow resistivity or select a thicker/denser sample so the normalized frequency parameter falls within 0.01-1.0'
    elif not physical:
        disposition='MODEL_RESULT_NONPHYSICAL_AT_THIS_THICKNESS_FREQUENCY'
        required_revisions=['INCREASE_SAMPLE_THICKNESS_OR_VERIFY_WITH_MEASURED_IMPEDANCE_TUBE_DATA']
        experiment='Measure normal-incidence absorption in an impedance tube at this exact thickness/frequency; the empirical fit is known to be unreliable here'
    elif target_met:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
        experiment='Measure normal-incidence absorption in an impedance tube at the same thickness and frequency to confirm the empirical prediction'
    else:
        disposition='TARGET_NOT_MET'
        required_revisions=['INCREASE_THICKNESS_OR_LOWER_FLOW_RESISTIVITY']
        experiment='Re-run at increased thickness or with a lower-flow-resistivity material and compare predicted absorption against the same target'
    return {'normalized_frequency_parameter':X,'model_applicable':applicable,
            'characteristic_impedance_real':zc.real,'characteristic_impedance_imag':zc.imag,
            'propagation_constant_real':gamma.real,'propagation_constant_imag':gamma.imag,
            'surface_impedance_real':zs.real,'surface_impedance_imag':zs.imag,
            'absorption_coefficient':alpha,'checks':[check],'disposition':disposition,
            'required_revisions':required_revisions,
            'counter_hypotheses':['edge or frame leakage inflating apparent absorption rather than the bulk material itself',
                'airspace or non-rigid backing assumed as sealed-rigid, biasing surface impedance',
                'measured flow resistivity differs from the datasheet nominal value used here'],
            'next_discriminating_experiment':experiment,
            'model_assumptions':['Delany-Bazley (1970) empirical fit, normal-incidence plane wave',
                'homogeneous, isotropic bulk material','rigid, sealed backing with no airspace',
                'general lossy transmission-line surface impedance Zs=Zc*coth(gamma*d)'],
            'unresolved':['measured/physical impedance-tube verification','oblique-incidence or diffuse-field (random-incidence) absorption',
                          'airspace-backed configuration']}


def sensor_fusion_doa_imu(params):
    """Inverse-variance circular fusion of an IMU-derived heading and an
    acoustic DOA estimate of the same true angle. Two well-established,
    independently-verifiable pieces, composed for this specific problem
    rather than one borrowed exotic model: (1) inverse-variance weighting
    is the standard minimum-variance linear combination of two
    independent noisy estimates (the same scalar Kalman-filter measurement
    update / GUM combined-uncertainty formula used elsewhere in this
    codebase); (2) the weighted circular mean (via unit-vector sum then
    atan2) is the standard way to average angles without a naive average
    breaking down across the 0/360 wrap boundary. Neither number is
    invented -- both are checked by hand against a plain non-circular
    weighted average for a nominal case with a small angular difference,
    where the two must nearly agree.

    A circular disagreement near 180 degrees is *not* auto-corrected --
    it is flagged as a possible frame-convention sign error (this role's
    own stated failure mode) instead of being fused into a number that
    happens to average two disagreeing sources into a false-confident
    middle. That is a real, current limitation of this baseline, not
    something masked."""
    schema=json.loads((ROOT/'skills/sensor-fusion-doa-imu-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact sensor-fusion SI-unit field contract required')
    for key,rules in schema['properties'].items():
        value=params[key]
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):
            raise ValueError('finite numeric value required: '+key)
        if value<rules.get('minimum',-math.inf) or value>rules.get('maximum',math.inf) or value<=rules.get('exclusiveMinimum',-math.inf):
            raise ValueError('invalid declared-unit value: '+key)
    p=params
    timestamp_skew=abs(p['imu_timestamp_s']-p['acoustic_timestamp_s'])
    w1=1/p['imu_heading_std_deg']**2; w2=1/p['acoustic_doa_std_deg']**2
    a1=math.radians(p['imu_heading_deg']); a2=math.radians(p['acoustic_doa_deg'])
    wx=w1*math.cos(a1)+w2*math.cos(a2); wy=w1*math.sin(a1)+w2*math.sin(a2)
    fused_heading=math.degrees(math.atan2(wy,wx))
    fused_std=math.sqrt(1/(w1+w2))
    circular_disagreement=math.degrees(math.atan2(math.sin(a1-a2),math.cos(a1-a2)))
    frame_reversal_suspected=abs(abs(circular_disagreement)-180)<=30
    timestamp_ok=timestamp_skew<=p['max_acceptable_timestamp_skew_s']
    precision_ok=fused_std<=p['max_acceptable_fused_std_deg']
    checks=[{'id':'TIMESTAMP_SKEW_S','actual':timestamp_skew,'limit':p['max_acceptable_timestamp_skew_s'],
             'margin':p['max_acceptable_timestamp_skew_s']-timestamp_skew,'operator':'<=','passed':bool(timestamp_ok),
             'on_failure':'RESYNCHRONIZE_IMU_AND_ACOUSTIC_CAPTURE_CLOCKS'},
            {'id':'FUSED_HEADING_STD_DEG','actual':fused_std,'limit':p['max_acceptable_fused_std_deg'],
             'margin':p['max_acceptable_fused_std_deg']-fused_std,'operator':'<=','passed':bool(precision_ok),
             'on_failure':'IMPROVE_IMU_OR_ACOUSTIC_DOA_PRECISION_BEFORE_FUSING'}]
    if frame_reversal_suspected:
        disposition='POSSIBLE_FRAME_CONVENTION_REVERSAL'
        required_revisions=['CONFIRM_IMU_AND_ACOUSTIC_HEADING_SHARE_THE_SAME_SIGN_CONVENTION_BEFORE_TRUSTING_THIS_FUSION']
        experiment='Physically rotate the device a known amount and confirm both IMU and acoustic DOA report consistent-sign changes'
    elif not timestamp_ok:
        disposition='EXCESSIVE_TIMESTAMP_SKEW'; required_revisions=[checks[0]['on_failure']]
        experiment='Repeat capture with hardware-synchronized IMU and acoustic timestamps, then re-fuse'
    elif not precision_ok:
        disposition='FUSED_UNCERTAINTY_EXCEEDS_TARGET'; required_revisions=[checks[1]['on_failure']]
        experiment='Repeat fusion across a short static sequence and confirm the fused heading standard deviation matches the predicted value here'
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
        experiment='Repeat fusion across a short static sequence and confirm the fused heading standard deviation matches the predicted value here'
    return {'timestamp_skew_s':timestamp_skew,'fused_heading_deg':fused_heading,'fused_heading_std_deg':fused_std,
            'circular_disagreement_deg':circular_disagreement,'frame_reversal_suspected':frame_reversal_suspected,
            'checks':checks,'disposition':disposition,'required_revisions':required_revisions,
            'counter_hypotheses':['sensor mounting/alignment offset rather than a true frame-convention sign error',
                'clock jitter rather than genuine angular motion between the two timestamps',
                'acoustic multipath or front-back ambiguity biasing the DOA estimate rather than IMU drift'],
            'next_discriminating_experiment':experiment,
            'model_assumptions':['both angles already expressed in the same coordinate convention; only a near-180-degree disagreement is screened as a possible sign error, not corrected automatically',
                'inverse-variance circular fusion is valid while both angular standard uncertainties stay well inside the small-angle regime',
                'the IMU and acoustic estimates are conditionally independent measurements of the same true heading'],
            'unresolved':['physical bench verification of the fused heading against a ground-truth reference',
                'non-Gaussian or multimodal DOA error (e.g. front-back ambiguity) not represented by a single standard deviation',
                'true clock-domain calibration between the IMU and acoustic capture paths']}


def binaural_itd_spherical_head(params):
    """Woodworth (1938) far-field spherical-head interaural time difference
    (ITD) approximation: ITD(theta) = (a/c)*(theta + sin(theta)) for the
    front hemisphere (0<=theta<=90 deg from the median plane), extended to
    the full circle by the sphere's own front-back and left-right
    symmetry. Cross-checked against a well-known real value before writing
    this: at theta=90 deg with a typical head radius (8.75cm) and
    c=343 m/s this gives ITD=655.8 microseconds, matching the commonly
    cited ~650-660 microsecond human maximum ITD -- this is not a fitted
    or invented number, it falls out of the formula directly.

    This is a baseline sanity check for a claimed/measured ITD from an
    HRTF or spatial-audio rendering pipeline, not a substitute for
    individualized HRTF measurement -- a real head is not a sphere, and
    pinna/torso effects this model excludes matter most exactly where
    this model is weakest (near +-90 degrees and above a few kHz)."""
    schema=json.loads((ROOT/'skills/binaural-itd-spherical-head-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact binaural ITD SI-unit field contract required')
    for key,rules in schema['properties'].items():
        value=params[key]
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):
            raise ValueError('finite numeric value required: '+key)
        if value<rules.get('minimum',-math.inf) or value>rules.get('maximum',math.inf) or value<=rules.get('exclusiveMinimum',-math.inf):
            raise ValueError('invalid declared-unit value: '+key)
    p=params
    azimuth=abs(p['azimuth_deg'])
    if azimuth>180: azimuth=360-azimuth
    effective=azimuth if azimuth<=90 else 180-azimuth
    effective_rad=math.radians(effective)
    predicted_itd_s=(p['head_radius_m']/p['sound_speed_m_s'])*(effective_rad+math.sin(effective_rad))
    predicted_itd_us=predicted_itd_s*1e6
    error_us=abs(p['claimed_itd_us']-predicted_itd_us)
    within_tolerance=error_us<=p['max_acceptable_itd_error_us']
    check={'id':'ITD_ERROR_US','actual':error_us,'limit':p['max_acceptable_itd_error_us'],
           'margin':p['max_acceptable_itd_error_us']-error_us,'operator':'<=','passed':bool(within_tolerance),
           'on_failure':'RECONCILE_CLAIMED_ITD_AGAINST_SPHERICAL_HEAD_BASELINE_OR_JUSTIFY_THE_DEVIATION'}
    disposition='BOUNDED_BASELINE_ACCEPT' if within_tolerance else 'ITD_MISMATCH_EXCEEDS_TOLERANCE'
    return {'effective_azimuth_deg':effective,'predicted_itd_us':predicted_itd_us,'itd_error_us':error_us,
            'checks':[check],'disposition':disposition,
            'required_revisions':[] if within_tolerance else [check['on_failure']],
            'counter_hypotheses':['individualized head/pinna geometry differing from the spherical-head approximation rather than a rendering defect',
                'incorrect azimuth convention (front/back or left/right reversal) rather than a genuine ITD error',
                'frequency-dependent HRTF phase behavior near or above the spatial-aliasing frequency, not captured by this low-frequency far-field model'],
            'next_discriminating_experiment':'Repeat the comparison at several azimuths spanning 0 to 90 degrees and check whether the error grows smoothly (model limits) or jumps at one azimuth (a data/convention defect)',
            'model_assumptions':['far-field plane-wave incidence on a rigid sphere','head modeled as a sphere; pinna, torso and individual head shape are excluded',
                'low-frequency approximation; interaural phase behavior above roughly 1.5kHz is not represented'],
            'unresolved':['physical or individualized-HRTF measurement of the true ITD','interaural level difference (ILD) and spectral pinna cues',
                          'frequency-dependent behavior across the full audible band']}


def tolerance_stack_rss(params):
    """Standard statistical dimensional-tolerance stack-up: worst-case
    (arithmetic sum, assumes every contributor sits at its extreme
    simultaneously) versus RSS/root-sum-square (assumes independent,
    normally-distributed contributors) -- textbook GD&T/tolerance-analysis
    method, sanity-checked against the classic 3-4-5 triangle
    (sqrt(3^2+4^2)=5) before writing this. The real engineering value is
    the DISCRIMINATION between the two: a stack that fails worst-case but
    passes RSS is a common, real, defensible middle ground (assuming the
    contributors really are independent), not a rounding artifact -- it
    gets its own disposition rather than being collapsed into a single
    pass/fail."""
    schema=json.loads((ROOT/'skills/tolerance-stack-rss-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact tolerance-stack SI-unit field contract required')
    contributors=params.get('contributor_tolerances_mm')
    rules=schema['properties']['contributor_tolerances_mm']
    if not isinstance(contributors,list) or not rules['minItems']<=len(contributors)<=rules['maxItems']:
        raise ValueError('bounded contributor tolerance list required')
    for value in contributors:
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or value<=0 or value>rules['items']['maximum']:
            raise ValueError('each contributor tolerance must be a finite, positive, bounded mm value')
    limit=params['maximum_acceptable_gap_mm']
    if isinstance(limit,bool) or not isinstance(limit,(float,int)) or not math.isfinite(limit) or limit<=0:
        raise ValueError('maximum_acceptable_gap_mm must be a finite positive value')
    worst_case=sum(contributors)
    rss=math.sqrt(sum(t*t for t in contributors))
    worst_case_ok=worst_case<=limit; rss_ok=rss<=limit
    checks=[{'id':'WORST_CASE_STACK_MM','actual':worst_case,'limit':limit,'margin':limit-worst_case,
             'operator':'<=','passed':bool(worst_case_ok),'on_failure':'REDUCE_CONTRIBUTOR_TOLERANCES_OR_COUNT'},
            {'id':'RSS_STACK_MM','actual':rss,'limit':limit,'margin':limit-rss,
             'operator':'<=','passed':bool(rss_ok),'on_failure':'REDUCE_CONTRIBUTOR_TOLERANCES_OR_VERIFY_INDEPENDENCE'}]
    if not rss_ok:
        disposition='TOLERANCE_STACK_EXCEEDS_SPEC_EVEN_STATISTICALLY'
        required_revisions=['REDUCE_CONTRIBUTOR_TOLERANCES_OR_COUNT_BEFORE_RELEASE']
    elif not worst_case_ok:
        disposition='WITHIN_STATISTICAL_RSS_BUT_NOT_WORST_CASE'
        required_revisions=['CONFIRM_CONTRIBUTORS_ARE_STATISTICALLY_INDEPENDENT_BEFORE_RELYING_ON_RSS']
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
    return {'worst_case_stack_mm':worst_case,'rss_stack_mm':rss,'checks':checks,'disposition':disposition,
            'required_revisions':required_revisions,
            'counter_hypotheses':['contributors are not actually statistically independent (shared datum or correlated process step) rather than genuinely independent',
                'declared values are specification limits rather than measured process capability (Cpk), overstating the true spread the RSS assumption expects',
                'a non-normal or skewed contributor distribution rather than the assumed near-normal spread'],
            'next_discriminating_experiment':'Measure the actual assembled-gap distribution across a real production sample and compare its standard deviation against the RSS prediction' if rss_ok else 'Identify which contributor(s) dominate the sum of squares and tighten those first',
            'model_assumptions':['contributor tolerances are independent random variables, not a worst-case guarantee','a near-normal distribution for each contributor, consistent with the RSS combination rule','no correlation from a shared datum, fixture, or process step across contributors'],
            'unresolved':['measured process capability (Cpk) for each contributor','physical assembled-sample verification of the combined distribution',
                          'correlation between contributors from a shared manufacturing datum']}


def audio_clock_drift_buffer_margin(params):
    """Digital-audio clock-drift buffer-margin baseline: given two audio
    clock domains' frequency error in ppm (parts-per-million -- a standard
    definition, error_hz/nominal_hz*1e6) and a shared-buffer resync
    interval, computes the accumulated sample drift and whether it
    exceeds the buffer's half-full margin before the next resync/ASRC
    correction. This is direct arithmetic from the ppm definition itself
    (drift_samples_per_s = sample_rate_hz * |ppm_a-ppm_b| * 1e-6), not a
    fitted or externally-sourced model -- hand-verified before writing
    this (e.g. 48000 Hz, 100 ppm relative error -> 4.8 samples/s drift)."""
    schema=json.loads((ROOT/'skills/audio-clock-drift-buffer-margin-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact clock-drift SI-unit field contract required')
    rules=schema['properties']
    sample_rate=params['nominal_sample_rate_hz']
    sample_rate_bound=rules['nominal_sample_rate_hz']
    if isinstance(sample_rate,bool) or not isinstance(sample_rate,(float,int)) or not math.isfinite(sample_rate) \
            or sample_rate<=sample_rate_bound['exclusiveMinimum'] or sample_rate>sample_rate_bound['maximum']:
        raise ValueError('nominal_sample_rate_hz must be a finite, positive, bounded Hz value')
    source_ppm=params['source_clock_ppm_error']
    sink_ppm=params['sink_clock_ppm_error']
    for name,value in (('source_clock_ppm_error',source_ppm),('sink_clock_ppm_error',sink_ppm)):
        bound=rules[name]
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or abs(value)>bound['maximum']:
            raise ValueError(f'{name} must be a finite, bounded ppm value')
    buffer_samples=params['buffer_size_samples']
    if isinstance(buffer_samples,bool) or not isinstance(buffer_samples,int) or buffer_samples<=0 or buffer_samples>rules['buffer_size_samples']['maximum']:
        raise ValueError('buffer_size_samples must be a positive bounded integer')
    resync_s=params['resync_interval_s']
    resync_bound=rules['resync_interval_s']
    if isinstance(resync_s,bool) or not isinstance(resync_s,(float,int)) or not math.isfinite(resync_s) \
            or resync_s<=resync_bound['exclusiveMinimum'] or resync_s>resync_bound['maximum']:
        raise ValueError('resync_interval_s must be a finite, positive, bounded second value')
    relative_ppm=abs(source_ppm-sink_ppm)
    drift_rate_samples_per_s=sample_rate*relative_ppm*1e-6
    accumulated_drift_samples=drift_rate_samples_per_s*resync_s
    half_buffer_samples=buffer_samples/2
    margin_samples=half_buffer_samples-accumulated_drift_samples
    time_to_exhaust_half_buffer_s=(half_buffer_samples/drift_rate_samples_per_s) if drift_rate_samples_per_s>0 else None
    margin_ok=bool(margin_samples>=0)
    checks=[{'id':'HALF_BUFFER_MARGIN_SAMPLES','actual':accumulated_drift_samples,'limit':half_buffer_samples,
             'margin':margin_samples,'operator':'<=','passed':margin_ok,
             'on_failure':'SHORTEN_RESYNC_INTERVAL_OR_ENABLE_ASRC_OR_INCREASE_BUFFER'}]
    if not margin_ok:
        disposition='BUFFER_MARGIN_EXCEEDED_BEFORE_RESYNC'
        required_revisions=['SHORTEN_RESYNC_INTERVAL_OR_ENABLE_CONTINUOUS_ASRC_OR_INCREASE_BUFFER_SIZE']
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
    return {'relative_ppm_error':relative_ppm,'drift_rate_samples_per_s':drift_rate_samples_per_s,
            'accumulated_drift_samples':accumulated_drift_samples,'margin_samples':margin_samples,
            'time_to_exhaust_half_buffer_s':time_to_exhaust_half_buffer_s,
            'checks':checks,'disposition':disposition,'required_revisions':required_revisions,
            'counter_hypotheses':['the two clocks are not actually free-running at their nominal ppm error but already share a hardware sync/PLL, making the assumed independent drift too pessimistic',
                'real clock error is not constant ppm but temperature- or aging-dependent, so the drift rate itself varies over the resync interval rather than staying fixed',
                'the OS/driver already runs continuous small-step resampling (ASRC) rather than a single hard resync at the end of the interval, understating the true available margin'],
            'next_discriminating_experiment':'Measure the real sample-count drift between the two clock domains over one full resync interval on the actual hardware/driver stack and compare against this prediction' if margin_ok else 'Identify whether the source or sink clock dominates the ppm error and correct or recalibrate that one first',
            'model_assumptions':['each clock domain has a constant, independent ppm frequency error over the resync interval','no continuous ASRC/resampling correction between resyncs','the buffer nominally sits half-full, so drift in either direction consumes the same half-buffer margin'],
            'unresolved':['measured real-hardware clock ppm error for the specific source/sink pair','whether the platform already performs continuous ASRC rather than periodic resync',
                          'temperature or aging dependence of the actual clock error']}


def erb_auditory_filter_bandwidth(params):
    """Equivalent Rectangular Bandwidth (ERB) auditory filter model,
    Glasberg & Moore (1990): ERB(f)=24.7*(4.37*f_kHz+1); ERB-rate (the
    Cams/ERB-number place on the auditory frequency scale)
    =21.4*log10(4.37*f_kHz+1). A standard, widely-cited psychoacoustic
    model of auditory-filter bandwidth, distinct from a listener's
    subjective loudness/annoyance preference -- checked here against a
    declared measured or claimed critical-bandwidth value. Hand-verified
    before use: ERB(1000 Hz)=132.639 Hz, matching the commonly cited
    ~132 Hz figure at 1 kHz in the auditory-modeling literature. Fitted
    range is documented as roughly 100 Hz-10 kHz; outside that the model
    is flagged rather than silently trusted."""
    schema=json.loads((ROOT/'skills/erb-auditory-filter-bandwidth-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact ERB SI-unit field contract required')
    rules=schema['properties']
    freq=params['center_frequency_hz']
    freq_bound=rules['center_frequency_hz']
    if isinstance(freq,bool) or not isinstance(freq,(float,int)) or not math.isfinite(freq) \
            or freq<=freq_bound['exclusiveMinimum'] or freq>freq_bound['maximum']:
        raise ValueError('center_frequency_hz must be a finite, positive, bounded Hz value')
    claimed=params['claimed_erb_hz']
    claimed_bound=rules['claimed_erb_hz']
    if isinstance(claimed,bool) or not isinstance(claimed,(float,int)) or not math.isfinite(claimed) \
            or claimed<=claimed_bound['exclusiveMinimum'] or claimed>claimed_bound['maximum']:
        raise ValueError('claimed_erb_hz must be a finite, positive, bounded Hz value')
    max_error=params['max_acceptable_error_hz']
    max_error_bound=rules['max_acceptable_error_hz']
    if isinstance(max_error,bool) or not isinstance(max_error,(float,int)) or not math.isfinite(max_error) \
            or max_error<=max_error_bound['exclusiveMinimum'] or max_error>max_error_bound['maximum']:
        raise ValueError('max_acceptable_error_hz must be a finite, positive, bounded Hz value')
    freq_khz=freq/1000.0
    predicted_erb_hz=24.7*(4.37*freq_khz+1)
    predicted_erb_rate=21.4*math.log10(4.37*freq_khz+1)
    model_applicable=bool(100.0<=freq<=10000.0)
    error_hz=abs(claimed-predicted_erb_hz)
    within_tolerance=bool(error_hz<=max_error)
    checks=[{'id':'ERB_MATCHES_MODEL','actual':error_hz,'limit':max_error,'margin':max_error-error_hz,
             'operator':'<=','passed':within_tolerance,'on_failure':'RECONCILE_CLAIMED_CRITICAL_BANDWIDTH_WITH_ERB_MODEL_OR_LISTENER_TEST'}]
    if not model_applicable:
        disposition='MODEL_OUTSIDE_FITTED_RANGE'
        required_revisions=['CONFIRM_ERB_MODEL_APPLICABILITY_OUTSIDE_100HZ_10KHZ_BEFORE_RELYING_ON_IT']
    elif not within_tolerance:
        disposition='CLAIMED_BANDWIDTH_DEVIATES_FROM_ERB_MODEL'
        required_revisions=['VERIFY_WHETHER_DEVIATION_REFLECTS_A_REAL_LISTENER_EFFECT_OR_A_MEASUREMENT_ERROR']
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
    return {'predicted_erb_hz':predicted_erb_hz,'predicted_erb_rate':predicted_erb_rate,
            'model_applicable':model_applicable,'error_hz':error_hz,
            'checks':checks,'disposition':disposition,'required_revisions':required_revisions,
            'counter_hypotheses':['the claimed bandwidth reflects a genuine measured psychoacoustic effect (e.g. off-frequency listening or individual variability) rather than an error',
                'the reference stimulus or masking paradigm used to derive the claimed value differs from the notched-noise paradigm the ERB model was fitted on',
                'the claimed value is itself a rounded or approximated figure rather than a directly measured critical bandwidth'],
            'next_discriminating_experiment':'Re-derive the critical bandwidth from a notched-noise masking measurement at this exact center frequency and compare directly to the ERB prediction' if not within_tolerance else 'Repeat at a second, well-separated frequency to confirm the model tracks bandwidth growth correctly across frequency, not just at one point',
            'model_assumptions':['the auditory filter is well-approximated by the Glasberg & Moore (1990) roex-based ERB fit','the claimed bandwidth was derived under conditions comparable to the standard notched-noise paradigm'],
            'unresolved':['individual listener variability in auditory filter width','whether the claimed value came from a calibrated psychoacoustic measurement or a secondary/approximate source']}


def thermal_noise_floor(params):
    """Johnson-Nyquist thermal noise voltage: Vrms=sqrt(4*k*T*R*BW),
    k=1.380649e-23 J/K (exact SI-defined Boltzmann constant). Standard
    textbook physics, not a fitted or acoustic-specific model -- gives the
    theoretical noise-floor MINIMUM a real resistor/bandwidth/temperature
    combination can ever produce, which any claimed measured system noise
    floor must sit at or above; a claim below it is a physical
    impossibility (wrong reference, wrong bandwidth, or a measurement
    error), not evidence of an unusually quiet circuit. The gap between a
    claimed floor and this minimum is the headroom available for real
    EMI/ground/clock coupling before it would show up above the
    irreducible thermal floor. Hand-verified before use: R=10 kOhm,
    T=298.15 K, BW=20 kHz -> Vrms=1814.7 nV, matching the commonly cited
    ~1.8 uV RMS figure for a 10 kOhm resistor over the audio band."""
    schema=json.loads((ROOT/'skills/thermal-noise-floor-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact thermal-noise SI-unit field contract required')
    rules=schema['properties']
    resistance=params['resistance_ohm']
    resistance_bound=rules['resistance_ohm']
    if isinstance(resistance,bool) or not isinstance(resistance,(float,int)) or not math.isfinite(resistance) \
            or resistance<=resistance_bound['exclusiveMinimum'] or resistance>resistance_bound['maximum']:
        raise ValueError('resistance_ohm must be a finite, positive, bounded Ohm value')
    temperature_c=params['temperature_c']
    temperature_bound=rules['temperature_c']
    if isinstance(temperature_c,bool) or not isinstance(temperature_c,(float,int)) or not math.isfinite(temperature_c) \
            or temperature_c<temperature_bound['minimum'] or temperature_c>temperature_bound['maximum']:
        raise ValueError('temperature_c must be a finite, bounded Celsius value')
    bandwidth=params['bandwidth_hz']
    bandwidth_bound=rules['bandwidth_hz']
    if isinstance(bandwidth,bool) or not isinstance(bandwidth,(float,int)) or not math.isfinite(bandwidth) \
            or bandwidth<=bandwidth_bound['exclusiveMinimum'] or bandwidth>bandwidth_bound['maximum']:
        raise ValueError('bandwidth_hz must be a finite, positive, bounded Hz value')
    claimed_v=params['claimed_noise_floor_v_rms']
    claimed_bound=rules['claimed_noise_floor_v_rms']
    if isinstance(claimed_v,bool) or not isinstance(claimed_v,(float,int)) or not math.isfinite(claimed_v) \
            or claimed_v<=claimed_bound['exclusiveMinimum'] or claimed_v>claimed_bound['maximum']:
        raise ValueError('claimed_noise_floor_v_rms must be a finite, positive, bounded volt value')
    k=1.380649e-23
    temperature_k=temperature_c+273.15
    thermal_floor_v_rms=math.sqrt(4*k*temperature_k*resistance*bandwidth)
    physically_consistent=bool(claimed_v>=thermal_floor_v_rms)
    excess_v_rms=claimed_v-thermal_floor_v_rms
    checks=[{'id':'CLAIMED_FLOOR_AT_OR_ABOVE_THERMAL_MINIMUM','actual':claimed_v,'limit':thermal_floor_v_rms,
             'margin':excess_v_rms,'operator':'>=','passed':physically_consistent,
             'on_failure':'CHECK_REFERENCE_BANDWIDTH_TEMPERATURE_OR_RESISTANCE_USED_FOR_THE_CLAIMED_FIGURE'}]
    if not physically_consistent:
        disposition='CLAIMED_NOISE_BELOW_THERMAL_FLOOR_IMPOSSIBLE'
        required_revisions=['RECONCILE_CLAIMED_NOISE_FLOOR_WITH_THE_DECLARED_RESISTANCE_TEMPERATURE_AND_BANDWIDTH_BEFORE_TRUSTING_IT']
    elif excess_v_rms/thermal_floor_v_rms>1.0:
        disposition='EXCESS_NOISE_LIKELY_NON_THERMAL_SOURCE'
        required_revisions=['INVESTIGATE_EMI_GROUND_LOOP_OR_CLOCK_COUPLING_AS_THE_DOMINANT_NOISE_CONTRIBUTOR']
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
    return {'thermal_floor_v_rms':thermal_floor_v_rms,'excess_v_rms':excess_v_rms,
            'physically_consistent':physically_consistent,
            'checks':checks,'disposition':disposition,'required_revisions':required_revisions,
            'counter_hypotheses':['the claimed figure uses a different reference bandwidth or termination than declared here, making a direct comparison invalid',
                'the excess noise above thermal is dominated by active-component (op-amp/ADC) noise rather than EMI or ground coupling',
                'the claimed value was measured with an unweighted or differently-weighted bandwidth (e.g. A-weighted) than the flat bandwidth assumed here'],
            'next_discriminating_experiment':'Terminate the input with the same resistance in a shielded enclosure and re-measure the noise floor in isolation from the rest of the signal chain to separate thermal from EMI/ground contributions' if physically_consistent else 'Re-derive the claimed noise figure from its original measurement bandwidth and reference before comparing again',
            'model_assumptions':['ideal resistor thermal noise only (no excess/flicker noise from real components)','a flat (unweighted) measurement bandwidth matching the declared value','room-temperature approximation is not assumed -- the declared temperature is used directly'],
            'unresolved':['contribution of active-component noise (op-amp, ADC) beyond the passive thermal floor','whether the claimed measurement bandwidth and weighting match the declared flat bandwidth']}


def correlation_statistical_support(params):
    """Fisher r-to-z transformation confidence interval for a claimed
    Pearson correlation between an objective metric and subjective MOS:
    z=atanh(r), SE_z=1/sqrt(n-3), 95% CI in z-space then transformed back
    via tanh. Standard textbook inferential statistics (Fisher 1921), used
    here to check whether a claimed metric-to-MOS correlation is even
    statistically distinguishable from zero at the declared sample size --
    directly on this role's mission of avoiding unsupported MOS-prediction
    claims, without computing MOS itself. Hand-verified before use: r=0.85,
    n=30 gives a 95% CI of about (0.706, 0.927) (excludes zero, supported);
    r=0.3, n=10 gives about (-0.406, 0.782) (includes zero, NOT
    statistically supported at that sample size)."""
    schema=json.loads((ROOT/'skills/correlation-statistical-support-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact correlation-support field contract required')
    rules=schema['properties']
    r=params['claimed_correlation_r']
    r_bound=rules['claimed_correlation_r']
    if isinstance(r,bool) or not isinstance(r,(float,int)) or not math.isfinite(r) \
            or r<=r_bound['exclusiveMinimum'] or r>=r_bound['exclusiveMaximum']:
        raise ValueError('claimed_correlation_r must be a finite value strictly between -1 and 1')
    n=params['sample_size']
    n_bound=rules['sample_size']
    if isinstance(n,bool) or not isinstance(n,int) or n<n_bound['minimum'] or n>n_bound['maximum']:
        raise ValueError('sample_size must be a bounded integer of at least 4')
    z_crit=1.959963984540054
    z=math.atanh(r)
    se_z=1/math.sqrt(n-3)
    lo_z=z-z_crit*se_z; hi_z=z+z_crit*se_z
    lo_r=math.tanh(lo_z); hi_r=math.tanh(hi_z)
    statistically_supported=bool(lo_r>0 or hi_r<0)
    checks=[{'id':'CONFIDENCE_INTERVAL_EXCLUDES_ZERO','actual':r,'limit':0.0,'margin':min(abs(lo_r),abs(hi_r)) if statistically_supported else 0.0,
             'operator':'!=','passed':statistically_supported,'on_failure':'INCREASE_SAMPLE_SIZE_OR_TREAT_CORRELATION_AS_UNSUPPORTED'}]
    if not statistically_supported:
        disposition='CORRELATION_NOT_STATISTICALLY_SUPPORTED_AT_THIS_SAMPLE_SIZE'
        required_revisions=['COLLECT_MORE_SAMPLES_BEFORE_CLAIMING_THIS_METRIC_PREDICTS_MOS']
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
    return {'fisher_z':z,'standard_error_z':se_z,'ci95_low_r':lo_r,'ci95_high_r':hi_r,
            'statistically_supported':statistically_supported,
            'checks':checks,'disposition':disposition,'required_revisions':required_revisions,
            'counter_hypotheses':['the underlying relationship is genuinely nonlinear, so a Pearson correlation understates a real predictive relationship',
                'the sample was not drawn independently (e.g. repeated measures on the same few stimuli), violating the independence assumption this interval relies on',
                'the claimed r is itself rounded or estimated rather than computed directly from the raw paired data'],
            'next_discriminating_experiment':'Collect additional independent stimulus/MOS pairs and recompute the interval; report whether it now excludes zero' if not statistically_supported else 'Validate on a held-out set of stimuli not used to originally estimate the correlation, to rule out overfitting to this sample',
            'model_assumptions':['the paired metric/MOS observations are independent and identically distributed','the underlying relationship is approximately linear (Pearson correlation, not a nonlinear association measure)'],
            'unresolved':['whether the sample was independently collected or contains repeated-measures structure','possible nonlinear relationship not captured by a linear correlation coefficient']}


def measurement_uncertainty_budget(params):
    """GUM-style (Guide to the Expression of Uncertainty in Measurement)
    combined and expanded uncertainty: combined standard uncertainty
    uc=sqrt(sum(ui^2)) treats declared component uncertainties as
    independent and combines them in quadrature (root-sum-square);
    expanded uncertainty U=k*uc with a declared coverage factor k
    (k=2 approximates ~95% coverage for a normal distribution). Standard
    textbook metrology, not a fitted or acoustic-specific model.
    Hand-verified before use: components [0.1,0.2,0.05], k=2 ->
    uc=0.229128..., U=0.458257...."""
    schema=json.loads((ROOT/'skills/measurement-uncertainty-budget-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact uncertainty-budget field contract required')
    components=params.get('uncertainty_components')
    rules=schema['properties']['uncertainty_components']
    if not isinstance(components,list) or not rules['minItems']<=len(components)<=rules['maxItems']:
        raise ValueError('bounded uncertainty-component list required')
    for value in components:
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or value<=0 or value>rules['items']['maximum']:
            raise ValueError('each uncertainty component must be a finite, positive, bounded value')
    k=params['coverage_factor']
    k_bound=schema['properties']['coverage_factor']
    if isinstance(k,bool) or not isinstance(k,(float,int)) or not math.isfinite(k) or k<k_bound['minimum'] or k>k_bound['maximum']:
        raise ValueError('coverage_factor must be a finite, bounded value')
    max_expanded=params['maximum_acceptable_expanded_uncertainty']
    max_bound=schema['properties']['maximum_acceptable_expanded_uncertainty']
    if isinstance(max_expanded,bool) or not isinstance(max_expanded,(float,int)) or not math.isfinite(max_expanded) \
            or max_expanded<=max_bound['exclusiveMinimum'] or max_expanded>max_bound['maximum']:
        raise ValueError('maximum_acceptable_expanded_uncertainty must be a finite, positive, bounded value')
    combined_standard_uncertainty=math.sqrt(sum(u*u for u in components))
    expanded_uncertainty=k*combined_standard_uncertainty
    within_budget=bool(expanded_uncertainty<=max_expanded)
    checks=[{'id':'EXPANDED_UNCERTAINTY_WITHIN_BUDGET','actual':expanded_uncertainty,'limit':max_expanded,
             'margin':max_expanded-expanded_uncertainty,'operator':'<=','passed':within_budget,
             'on_failure':'REDUCE_DOMINANT_UNCERTAINTY_COMPONENT_OR_LOWER_COVERAGE_FACTOR_WITH_JUSTIFICATION'}]
    if not within_budget:
        disposition='EXPANDED_UNCERTAINTY_EXCEEDS_BUDGET'
        required_revisions=['IDENTIFY_AND_REDUCE_THE_DOMINANT_UNCERTAINTY_COMPONENT_BEFORE_RELEASE']
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
    return {'combined_standard_uncertainty':combined_standard_uncertainty,'expanded_uncertainty':expanded_uncertainty,
            'checks':checks,'disposition':disposition,'required_revisions':required_revisions,
            'counter_hypotheses':['the declared components are not actually statistically independent (shared calibration reference or correlated systematic effects), making RSS combination understate the true uncertainty',
                'a component was itself declared as an expanded (not standard) uncertainty, double-counting the coverage factor',
                'the true distribution is non-normal (e.g. rectangular for a Type B bound), making the k=2 approximate-95%-coverage assumption inexact'],
            'next_discriminating_experiment':'Perform a gage R&R or interlaboratory comparison to empirically verify the combined uncertainty against a real repeated-measurement spread' if within_budget else 'Identify which single component dominates the sum of squares and investigate reducing or better characterizing it first',
            'model_assumptions':['each declared uncertainty component is already expressed as a standard uncertainty (1-sigma-equivalent), not already expanded','the components are independent random variables, combined in quadrature','a coverage factor of k=2 approximates 95% coverage for a normal distribution'],
            'unresolved':['whether the declared components are truly statistically independent','empirical validation via gage R&R or interlaboratory comparison','whether any component distribution is significantly non-normal']}


def audio_path_latency_budget(params):
    """End-to-end real-time audio path latency budget: simple additive sum
    of encode, packetization, network, jitter-buffer, decode and output-
    buffer delays, checked against the ITU-T G.114 recommended maximum
    one-way transmission time for acceptable conversational quality
    (commonly cited as 150 ms one-way before echo/talker-overlap
    perceptibly degrades). Plain arithmetic, not a codec-specific or
    fitted model. Hand-verified before use: 20+20+40+60+5+10=155 ms,
    exceeding the 150 ms ITU-T G.114 guideline by 5 ms."""
    schema=json.loads((ROOT/'skills/audio-path-latency-budget-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact latency-budget field contract required')
    rules=schema['properties']
    components={}
    for name in ('encode_delay_ms','packetization_delay_ms','network_one_way_delay_ms','jitter_buffer_delay_ms','decode_delay_ms','output_buffer_delay_ms'):
        value=params[name]
        bound=rules[name]
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) \
                or value<bound['minimum'] or value>bound['maximum']:
            raise ValueError(f'{name} must be a finite, non-negative, bounded millisecond value')
        components[name]=value
    total_one_way_ms=sum(components.values())
    itu_t_g114_threshold_ms=150.0
    within_recommendation=bool(total_one_way_ms<=itu_t_g114_threshold_ms)
    checks=[{'id':'ONE_WAY_LATENCY_WITHIN_ITU_T_G114','actual':total_one_way_ms,'limit':itu_t_g114_threshold_ms,
             'margin':itu_t_g114_threshold_ms-total_one_way_ms,'operator':'<=','passed':within_recommendation,
             'on_failure':'REDUCE_JITTER_BUFFER_OR_NETWORK_DELAY_OR_ACCEPT_DEGRADED_CONVERSATIONAL_QUALITY'}]
    if not within_recommendation:
        disposition='LATENCY_EXCEEDS_ITU_T_G114_RECOMMENDATION'
        required_revisions=['IDENTIFY_AND_REDUCE_THE_DOMINANT_LATENCY_CONTRIBUTOR_BEFORE_RELEASE']
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
    return {'total_one_way_latency_ms':total_one_way_ms,'itu_t_g114_threshold_ms':itu_t_g114_threshold_ms,
            'component_breakdown_ms':components,
            'checks':checks,'disposition':disposition,'required_revisions':required_revisions,
            'counter_hypotheses':['the declared jitter-buffer delay is a fixed nominal value rather than the real adaptive value under actual network conditions, understating true worst-case latency',
                'the 150 ms ITU-T G.114 figure is a general conversational-quality guideline, not a hard requirement for this specific application (e.g. one-directional media streaming has no such constraint)',
                'round-trip (not one-way) latency is the actually relevant quantity for this use case, which this one-way budget does not directly address'],
            'next_discriminating_experiment':'Measure the real end-to-end latency on the actual device/network path (e.g. via a loopback timestamp test) and compare against this budgeted estimate' if within_recommendation else 'Identify which single stage (encode, network, jitter buffer, decode) dominates the total and target that stage for reduction first',
            'model_assumptions':['each stage delay is a fixed, declared value rather than a measured statistical distribution','the components are additive with no overlap or pipelining between stages','one-way (not round-trip) latency is the relevant quantity for the ITU-T G.114 comparison'],
            'unresolved':['real measured end-to-end latency under actual network conditions','whether the application context (conversational vs. one-directional) makes the ITU-T G.114 threshold applicable at all']}


def doe_two_sample_size(params):
    """Standard two-sample mean-comparison sample-size formula (normal
    approximation): n=2*(z_alpha/2+z_beta)^2*sigma^2/delta^2, where
    z_alpha/2 and z_beta are standard-normal quantiles for the declared
    two-sided significance level and statistical power. Standard textbook
    experimental-design statistics, not a fitted or acoustic-specific
    model. Hand-verified before use: sigma=5, delta=2, alpha=0.05,
    power=0.8 -> z_alpha/2=1.959964, z_beta=0.841621, n=98.11 (round up to
    99 per sample)."""
    from statistics import NormalDist
    schema=json.loads((ROOT/'skills/doe-two-sample-size-baseline/input.schema.json').read_text())
    if not isinstance(params,dict) or set(params)!=set(schema['required']):
        raise ValueError('exact DOE sample-size field contract required')
    rules=schema['properties']
    sigma=params['assumed_standard_deviation']
    sigma_bound=rules['assumed_standard_deviation']
    if isinstance(sigma,bool) or not isinstance(sigma,(float,int)) or not math.isfinite(sigma) \
            or sigma<=sigma_bound['exclusiveMinimum'] or sigma>sigma_bound['maximum']:
        raise ValueError('assumed_standard_deviation must be a finite, positive, bounded value')
    delta=params['minimum_detectable_difference']
    delta_bound=rules['minimum_detectable_difference']
    if isinstance(delta,bool) or not isinstance(delta,(float,int)) or not math.isfinite(delta) \
            or delta<=delta_bound['exclusiveMinimum'] or delta>delta_bound['maximum']:
        raise ValueError('minimum_detectable_difference must be a finite, positive, bounded value')
    alpha=params['significance_level_alpha']
    alpha_bound=rules['significance_level_alpha']
    if isinstance(alpha,bool) or not isinstance(alpha,(float,int)) or not math.isfinite(alpha) \
            or alpha<=alpha_bound['exclusiveMinimum'] or alpha>=alpha_bound['exclusiveMaximum']:
        raise ValueError('significance_level_alpha must be a finite value strictly between 0 and 1')
    power=params['statistical_power']
    power_bound=rules['statistical_power']
    if isinstance(power,bool) or not isinstance(power,(float,int)) or not math.isfinite(power) \
            or power<=power_bound['exclusiveMinimum'] or power>=power_bound['exclusiveMaximum']:
        raise ValueError('statistical_power must be a finite value strictly between 0 and 1')
    max_affordable_n=params['maximum_affordable_sample_size_per_group']
    max_n_bound=rules['maximum_affordable_sample_size_per_group']
    if isinstance(max_affordable_n,bool) or not isinstance(max_affordable_n,int) \
            or max_affordable_n<max_n_bound['minimum'] or max_affordable_n>max_n_bound['maximum']:
        raise ValueError('maximum_affordable_sample_size_per_group must be a bounded positive integer')
    dist=NormalDist()
    z_alpha=dist.inv_cdf(1-alpha/2)
    z_beta=dist.inv_cdf(power)
    required_n_exact=2*((z_alpha+z_beta)**2)*(sigma**2)/(delta**2)
    required_n_per_group=math.ceil(required_n_exact)
    affordable=bool(required_n_per_group<=max_affordable_n)
    checks=[{'id':'REQUIRED_SAMPLE_SIZE_WITHIN_BUDGET','actual':required_n_per_group,'limit':max_affordable_n,
             'margin':max_affordable_n-required_n_per_group,'operator':'<=','passed':affordable,
             'on_failure':'INCREASE_SAMPLE_BUDGET_OR_ACCEPT_A_LARGER_MINIMUM_DETECTABLE_DIFFERENCE_OR_LOWER_POWER'}]
    if not affordable:
        disposition='REQUIRED_SAMPLE_SIZE_EXCEEDS_BUDGET'
        required_revisions=['RELAX_MINIMUM_DETECTABLE_DIFFERENCE_OR_POWER_OR_INCREASE_SAMPLE_BUDGET_BEFORE_RUNNING_THE_EXPERIMENT']
    else:
        disposition='BOUNDED_BASELINE_ACCEPT'; required_revisions=[]
    return {'z_alpha_half':z_alpha,'z_beta':z_beta,'required_n_per_group_exact':required_n_exact,
            'required_n_per_group':required_n_per_group,'affordable':affordable,
            'checks':checks,'disposition':disposition,'required_revisions':required_revisions,
            'counter_hypotheses':['the assumed standard deviation is a guess or a pooled figure from a different population, so the true required sample size could be substantially larger or smaller',
                'the actual comparison will use a non-normal test (e.g. a rank-based test) whose required sample size differs from this normal-approximation formula',
                'unequal variance or unequal group sizes between the two arms would change the required sample size from this equal-variance, equal-n formula'],
            'next_discriminating_experiment':'Run a small pilot study to obtain a real estimate of the standard deviation before committing to the full experiment sample size' if affordable else 'Reduce scope (a larger acceptable minimum detectable difference or lower required power) or negotiate a larger sample budget',
            'model_assumptions':['approximately normally distributed outcome in both groups','equal variance and equal sample size assumed in both groups','the declared standard deviation is a reasonable prior estimate, not a guess with unknown error'],
            'unresolved':['whether the assumed standard deviation reflects the true population variability','whether the planned statistical test will actually be this normal-approximation two-sample comparison']}


from .microphone_domain import analyze as microphone_measurement
from .speaker_fr import analyze as speaker_fr_measurement
from .array_doa import analyze as array_doa_measurement
from .faca import analyze as failure_hypothesis_model
from .requirement_trace import analyze as requirement_association_model
from .standard_metadata import analyze as standards_metadata_model
from .sealed_alignment import analyze as sealed_alignment_model
from .array_beam import analyze as array_beam_model
from .capture_clock import analyze as capture_clock_model
from .ported_alignment import analyze as ported_alignment_model
from .speaker_polar import analyze as speaker_polar_model
from .speaker_tonal import analyze as speaker_tonal_model
from .speaker_signal_chain import analyze as speaker_signal_chain_model
from .speaker_bass_limiter import analyze as speaker_bass_limiter_model
from .structural_acoustic import analyze as structural_acoustic_model
from .room_decay import analyze as room_decay_model
from .room_correction import analyze as room_correction_model
from .speaker_digital_transport import analyze as speaker_digital_transport_model
from .reliability_halt import analyze as reliability_halt_model
from .factory_eol_capability import analyze as factory_eol_capability_model
from .instrument_sequence_safety import analyze as instrument_sequence_safety_model
from .incoming_lot_sampling import analyze as incoming_lot_sampling_model
from .next_experiment_safety import analyze as next_experiment_safety_model
from .test_automation_result_screening import analyze as test_automation_result_screening_model
from .doe_monte_carlo_design_screening import analyze as doe_monte_carlo_design_screening_model
from .vr_xr_headset_screening import analyze as vr_xr_headset_screening_model
from .automotive_cabin_tuning_screening import analyze as automotive_cabin_tuning_screening_model
from .amr_warning_doa_screening import analyze as amr_warning_doa_screening_model
from .quadruped_capture_screening import analyze as quadruped_capture_screening_model
from .humanoid_interaction_screening import analyze as humanoid_interaction_screening_model
from .conference_array_aec_screening import analyze as conference_array_aec_screening_model
from .directional_mic_array_screening import analyze as directional_mic_array_screening_model
from .codec_transport_screening import analyze as codec_transport_screening_model
from .audio_ml_evaluation_screening import analyze as audio_ml_evaluation_screening_model
from .acoustic_dataset_screening import analyze as acoustic_dataset_screening_model
from .benchmark_teardown_screening import analyze as benchmark_teardown_screening_model
from .patent_prior_art_screening import analyze as patent_prior_art_screening_model
from .research_hypothesis_screening import analyze as research_hypothesis_screening_model
from .speaker_filter_realization import analyze as speaker_filter_realization_model
from .microphone_architecture import analyze as microphone_architecture_model
from .far_field_scenarios import analyze as far_field_scenarios_model
from .microphone_tonal import analyze as microphone_tonal_model
from .aec_control import analyze as aec_control_model
from .hearing_aid_product import analyze as hearing_aid_product_model,analyze_otc as otc_self_fit_model
from .auracast_product import analyze as auracast_product_model
from .overear_anc_product import analyze as overear_anc_product_model
from .personal_device_products import (analyze_gaming as gaming_headset_model,analyze_smartphone as smartphone_product_model,
                                       analyze_tablet as tablet_product_model,analyze_laptop as laptop_product_model)
from .conference_products import analyze_monitor as monitor_product_model,analyze_smart_speaker as smart_speaker_product_model
from .av_products import analyze_soundbar as soundbar_product_model,analyze_theater as theater_product_model
from .environment_products import (analyze_tv as tv_product_model,analyze_doorbell as doorbell_product_model,
                                   analyze_appliance as appliance_product_model,analyze_open_ear as open_ear_product_model)

HANDLERS={'tws-fit-anc-call-baseline':tws_fit_anc_call,'speaker-power-distortion-baseline':speaker_power_distortion,
          'porous-material-absorption-baseline':porous_material_absorption,
          'sensor-fusion-doa-imu-baseline':sensor_fusion_doa_imu,
          'binaural-itd-spherical-head-baseline':binaural_itd_spherical_head,
          'tolerance-stack-rss-baseline':tolerance_stack_rss,
          'audio-clock-drift-buffer-margin-baseline':audio_clock_drift_buffer_margin,
          'erb-auditory-filter-bandwidth-baseline':erb_auditory_filter_bandwidth,
          'thermal-noise-floor-baseline':thermal_noise_floor,
          'correlation-statistical-support-baseline':correlation_statistical_support,
          'measurement-uncertainty-budget-baseline':measurement_uncertainty_budget,
          'audio-path-latency-budget-baseline':audio_path_latency_budget,
          'doe-two-sample-size-baseline':doe_two_sample_size,
          'microphone-reference-noise-headroom-baseline':microphone_measurement,
          'speaker-fr-reference-baseline':speaker_fr_measurement,
          'microphone-array-tdoa-baseline':array_doa_measurement,
          'failure-hypothesis-experiment-baseline':failure_hypothesis_model,
          'requirement-association-baseline':requirement_association_model,
          'standards-metadata-applicability-baseline':standards_metadata_model,
          'speaker-sealed-alignment-baseline':sealed_alignment_model,
          'speaker-ported-alignment-baseline':ported_alignment_model,
          'speaker-polar-spatial-baseline':speaker_polar_model,
          'speaker-tonal-eq-baseline':speaker_tonal_model,
          'speaker-signal-chain-noise-headroom-baseline':speaker_signal_chain_model,
          'speaker-bass-limiter-envelope-baseline':speaker_bass_limiter_model,
          'structural-acoustic-transfer-baseline':structural_acoustic_model,
          'room-decay-spatial-baseline':room_decay_model,
          'room-correction-spatial-baseline':room_correction_model,
          'speaker-digital-transport-baseline':speaker_digital_transport_model,
          'reliability-halt-screening-baseline':reliability_halt_model,
          'factory-eol-capability-screening-baseline':factory_eol_capability_model,
          'instrument-sequence-safety-screening-baseline':instrument_sequence_safety_model,
          'incoming-lot-sampling-screening-baseline':incoming_lot_sampling_model,
          'next-experiment-safety-screening-baseline':next_experiment_safety_model,
          'test-automation-result-screening-baseline':test_automation_result_screening_model,
          'doe-monte-carlo-design-screening-baseline':doe_monte_carlo_design_screening_model,
          'vr-xr-headset-screening-baseline':vr_xr_headset_screening_model,
          'automotive-cabin-tuning-screening-baseline':automotive_cabin_tuning_screening_model,
          'amr-warning-doa-screening-baseline':amr_warning_doa_screening_model,
          'quadruped-capture-screening-baseline':quadruped_capture_screening_model,
          'humanoid-interaction-screening-baseline':humanoid_interaction_screening_model,
          'conference-array-aec-screening-baseline':conference_array_aec_screening_model,
          'directional-mic-array-screening-baseline':directional_mic_array_screening_model,
          'codec-transport-screening-baseline':codec_transport_screening_model,
          'audio-ml-evaluation-screening-baseline':audio_ml_evaluation_screening_model,
          'acoustic-dataset-screening-baseline':acoustic_dataset_screening_model,
          'benchmark-teardown-screening-baseline':benchmark_teardown_screening_model,
          'patent-prior-art-screening-baseline':patent_prior_art_screening_model,
          'research-hypothesis-screening-baseline':research_hypothesis_screening_model,
          'speaker-filter-realization-baseline':speaker_filter_realization_model,
          'microphone-architecture-baseline':microphone_architecture_model,
          'microphone-far-field-scenarios-baseline':far_field_scenarios_model,
          'microphone-tonal-headroom-baseline':microphone_tonal_model,
          'microphone-aec-control-baseline':aec_control_model,
          'hearing-aid-gain-feedback-output-baseline':hearing_aid_product_model,
          'otc-self-fit-output-baseline':otc_self_fit_model,
          'auracast-latency-sync-baseline':auracast_product_model,
          'over-ear-anc-seal-stability-baseline':overear_anc_product_model,
          'gaming-headset-communication-baseline':gaming_headset_model,
          'smartphone-port-mesh-echo-baseline':smartphone_product_model,
          'tablet-orientation-case-table-baseline':tablet_product_model,
          'laptop-fan-hinge-coupling-baseline':laptop_product_model,
          'monitor-aio-usb-desk-baseline':monitor_product_model,
          'smart-speaker-far-field-self-echo-baseline':smart_speaker_product_model,
          'soundbar-crossover-wall-dialogue-baseline':soundbar_product_model,
          'home-theater-level-polarity-delay-baseline':theater_product_model,
          'thin-tv-panel-wall-dialogue-baseline':tv_product_model,
          'doorbell-weather-intercom-baseline':doorbell_product_model,
          'appliance-motor-notification-voice-baseline':appliance_product_model,
          'ar-open-ear-leakage-tracking-wind-baseline':open_ear_product_model,
          'microphone-array-taper-baseline':array_beam_model,
          'microphone-capture-continuity-baseline':capture_clock_model}

_CAPABILITY_DEPENDENCIES={
    'microphone-reference-noise-headroom-baseline':('numerical_policy.py',),
    'speaker-fr-reference-baseline':('numerical_policy.py',),
    'microphone-array-tdoa-baseline':('numerical_policy.py',),
}


def _runtime_dependency_payload(skill_id):
    if skill_id=='microphone-reference-noise-headroom-baseline':
        from . import microphone_domain as module
        values=(module.db_at_least,module.db_at_most,module.MIN_IDENTIFIABLE_VARIANCE_FRACTION)
    elif skill_id=='speaker-fr-reference-baseline':
        from . import speaker_fr as module
        values=(module.db_at_least,module.db_at_most,module.cycles_at_least)
    elif skill_id=='microphone-array-tdoa-baseline':
        from . import array_doa as module
        values=(module.ratio_at_least,module.geometry_value)
    else: values=()
    result=[]
    for value in values:
        result.append(inspect.getsource(value) if callable(value) else value)
    return result


def _review_handler(domain):
    def run(params):
        from .domain_review import review
        return review(domain,params)
    return run


for _domain in ('speaker-nonlinear','speaker-thermal','tws-anc','tws-fit-capture','microphone-reference','microphone-noise-headroom','speaker-fr-uncertainty','microphone-array-geometry','failure-hypothesis','requirement-association','standards-metadata','speaker-sealed-lumped','speaker-port-lumped','speaker-polar-spatial','speaker-tonal-context','speaker-signal-chain-headroom','speaker-bass-protection','structural-acoustic-path','room-decay-spatial','room-correction-spatial','speaker-digital-transport','speaker-filter-realization','microphone-architecture-acoustic-path','microphone-far-field-disturbance','microphone-tonal-intelligibility','microphone-aec-enhancement','hearing-aid-acoustic-boundary','otc-self-fit-output-claims','auracast-transport-sync','over-ear-anc-seal-stability','gaming-communication-latency','smartphone-port-mesh-echo','tablet-orientation-case-table','laptop-fan-hinge-coupling','monitor-aio-usb-desk','smart-speaker-far-field-self-echo','soundbar-crossover-wall-dialogue','home-theater-level-polarity-delay','thin-tv-panel-wall-dialogue','doorbell-weather-intercom','appliance-motor-notification-voice','ar-open-ear-leakage-tracking-wind','microphone-array-pattern','microphone-capture-clock'):
    HANDLERS[_domain+'-domain-review']=_review_handler(_domain)


def capability_source_digest(skill_id):
    """Fingerprint one handler and only the shared predicates it can invoke."""
    if skill_id not in HANDLERS: raise KeyError(skill_id)
    handler=HANDLERS[skill_id]; module=inspect.getmodule(handler)
    try: source=inspect.getsource(handler)
    except (OSError,TypeError) as exc: raise ValueError('inspectable capability source required') from exc
    payload={'skill_id':skill_id,'handler_module':getattr(module,'__name__',None),'handler_source':source}
    if module is not None and module.__name__!=__name__:
        path=Path(inspect.getsourcefile(handler) or '')
        if not path.is_file(): raise ValueError('capability implementation source missing')
        payload['dedicated_module_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        payload['shared_dependencies']={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                                        for name in _CAPABILITY_DEPENDENCIES.get(skill_id,())}
        payload['runtime_dependencies']=_runtime_dependency_payload(skill_id)
    elif handler.__name__=='run':
        # The closure value binds the exact review domain. Its current behavior
        # is additionally replayed against every sealed suite case, so a changed
        # relevant verdict stales the receipt without coupling unrelated review
        # branches in the same policy module.
        closure=list(inspect.getclosurevars(handler).nonlocals.values())
        payload['closure']=closure
        if len(closure)!=1 or not isinstance(closure[0],str): raise ValueError('exact review-domain closure required')
        from . import domain_review
        payload['domain_review_sha256']=domain_review.capability_source_digest(closure[0])
    elif skill_id=='tws-fit-anc-call-baseline':
        payload['field_contract']=TWS_FIELDS
    return hashlib.sha256(_canonical(payload)).hexdigest()


def execute(skill_id,params):
    if _fingerprint()!=LOADED_SHA256: raise RuntimeError('Role method source changed after load; restart required')
    if skill_id not in HANDLERS: raise KeyError(skill_id)
    values=HANDLERS[skill_id](params)
    _canonical(values)  # Nonfinite calculation results must never leave as PASS.
    return {'skill_id':skill_id,'version':'1.0.0','result':'PASS','values':values,
            'input_sha256':hashlib.sha256(_canonical(params)).hexdigest(),
            'implementation_sha256':capability_source_digest(skill_id),
            'capability_maturity':'FREE_LOCAL_BASELINE','evidence_class':'DETERMINISTIC_ROLE_DOMAIN_CALCULATION',
            'uncertainty':'Supplied model parameters and limits are uncalibrated unless separately evidenced; see model assumptions.',
            'physical_measurement_verified':False,'professional_tool_verified':False,
            'truth':'Calculation completion is not role L3, physical acceptance, or product certification.'}


LOADED_SHA256=_fingerprint()
