"""Bounded sampled ULA transfer, mismatch intervals and white-noise gain."""
import cmath
import math

SCALARS={'spacing_m':(1e-5,10),'steering_deg':(-90,90),'sound_speed_m_s':(200,500),
    'source_range_m':(1e-4,1e5),'minimum_range_aperture_ratio':(2,100),
    'minimum_fraunhofer_ratio':(1,100),'main_lobe_exclusion_deg':(0,89),
    'maximum_grid_gap_deg':(0.1,90),'minimum_desired_amplitude':(0,100),
    'maximum_sampled_sidelobe_amplitude':(0,100),'minimum_white_noise_gain':(0,32)}
VECTORS={'weights':(0,1e6),'channel_gains':(1e-4,100),'channel_delays_s':(-0.1,0.1),
    'gain_bounds':(0,100),'delay_bounds_s':(0,0.1),'position_bounds_m':(0,10),
    'frequencies_hz':(1,96000),'angles_deg':(-90,90)}


def validate(p):
    if not isinstance(p,dict) or set(p)!=set(SCALARS)|set(VECTORS)|{'model','noise_model'}:
        raise ValueError('exact ULA SI-unit input contract required')
    if p['model']!='FAR_FIELD_ULA_TRUE_TIME_DELAY' or p['noise_model']!='UNCORRELATED_EQUAL_VARIANCE_BEFORE_GAIN':
        raise ValueError('unsupported geometry or cross-channel noise covariance')
    def finite(value,limits):
        return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value) and limits[0]<=value<=limits[1]
    for key,limits in SCALARS.items():
        if not finite(p[key],limits):raise ValueError('invalid scalar '+key)
    for key,limits in VECTORS.items():
        size=(1,128) if key=='frequencies_hz' else (3,721) if key=='angles_deg' else (2,32)
        if not isinstance(p[key],list) or not size[0]<=len(p[key])<=size[1] or not all(finite(v,limits) for v in p[key]):
            raise ValueError('invalid bounded vector '+key)
    n=len(p['weights'])
    if sum(p['weights'])<=0 or any(len(p[k])!=n for k in VECTORS if k not in {'angles_deg','frequencies_hz'}):
        raise ValueError('nonzero matched element vectors required')
    if any(e>=g for e,g in zip(p['gain_bounds'],p['channel_gains'])):
        raise ValueError('gain intervals must remain positive')
    if any(e>=p['spacing_m']/2 for e in p['position_bounds_m']):
        raise ValueError('position uncertainty must preserve element ordering')
    for key in ('angles_deg','frequencies_hz'):
        if any(b<=a for a,b in zip(p[key],p[key][1:])):raise ValueError('strictly ordered grid required')
    if p['angles_deg'][0]!=-90 or p['angles_deg'][-1]!=90:
        raise ValueError('angle grid must span the declared hemisphere')
    if not any(abs(a-p['steering_deg'])>p['main_lobe_exclusion_deg'] for a in p['angles_deg']):
        raise ValueError('at least one sidelobe sample required')


def analyze(parameters):
    validate(parameters);p=parameters;n=len(p['weights']);total=math.fsum(p['weights'])
    weights=[a/total for a in p['weights']]
    angles=sorted(set(p['angles_deg']+[p['steering_deg']]))
    direction=math.sin(math.radians(p['steering_deg']));c=p['sound_speed_m_s']
    noise=math.fsum((a*g)**2 for a,g in zip(weights,p['channel_gains']))
    noise_upper=math.fsum((a*(g+e))**2 for a,g,e in zip(weights,p['channel_gains'],p['gain_bounds']))
    def response(f,angle):
        sine=math.sin(math.radians(angle));parts=[];errors=[]
        for i,a in enumerate(weights):
            phase=2*math.pi*f*(i*p['spacing_m']*(sine-direction)/c-p['channel_delays_s'][i])
            parts.append(a*p['channel_gains'][i]*cmath.exp(1j*phase))
            bound=2*math.pi*f*(p['position_bounds_m'][i]*abs(sine)/c+p['delay_bounds_s'][i])
            errors.append(a*(p['gain_bounds'][i]+2*p['channel_gains'][i]*math.sin(min(bound,math.pi)/2)))
        value=complex(math.fsum(v.real for v in parts),math.fsum(v.imag for v in parts))
        amplitude=abs(value);error=math.fsum(errors)
        return amplitude,max(0,amplitude-error),amplitude+error
    bands=[]
    for f in p['frequencies_hz']:
        samples=[response(f,a) for a in angles];desired=response(f,p['steering_deg'])
        sidelobes=[s[2] for a,s in zip(angles,samples) if abs(a-p['steering_deg'])>p['main_lobe_exclusion_deg']]
        bands.append({'frequency_hz':f,'sample_amplitudes':[s[0] for s in samples],
            'sample_lower':[s[1] for s in samples],'sample_upper':[s[2] for s in samples],
            'desired_amplitude':desired[0],'desired_lower':desired[1],'desired_upper':desired[2],
            'sampled_sidelobe_upper':max(sidelobes),'white_noise_gain':desired[0]**2/noise,
            'white_noise_gain_lower':desired[1]**2/noise_upper})
    aperture=(n-1)*p['spacing_m']+p['position_bounds_m'][0]+p['position_bounds_m'][-1]
    largest_spacing=max(p['spacing_m']+p['position_bounds_m'][i]+p['position_bounds_m'][i+1] for i in range(n-1))
    alias_spacing=c/(2*p['frequencies_hz'][-1])
    fraunhofer=2*aperture**2*p['frequencies_hz'][-1]/c
    range_required=max(aperture*p['minimum_range_aperture_ratio'],fraunhofer*p['minimum_fraunhofer_ratio'])
    gap=max(b-a for a,b in zip(angles,angles[1:]))
    rows=[('SPATIAL_SAMPLING_GUARD',largest_spacing,alias_spacing,largest_spacing<=alias_spacing,'REDUCE_SPACING_OR_DECLARED_BAND'),
          ('FAR_FIELD_HEURISTIC',p['source_range_m'],range_required,p['source_range_m']>=range_required,'USE_NEAR_FIELD_PROPAGATION_OR_INCREASE_RANGE'),
          ('ANGULAR_SAMPLING',gap,p['maximum_grid_gap_deg'],gap<=p['maximum_grid_gap_deg'],'REFINE_ANGULAR_GRID_WITHOUT_CLAIMING_CONTINUOUS_COVERAGE'),
          ('DESIRED_GAIN_BOUND',min(b['desired_lower'] for b in bands),p['minimum_desired_amplitude'],
           all(round(b['desired_lower'],12)>=round(p['minimum_desired_amplitude'],12) for b in bands),'RECALIBRATE_CHANNEL_GAIN_DELAY_OR_REVISE_STEERING'),
          ('SAMPLED_SIDELOBE_BOUND',max(b['sampled_sidelobe_upper'] for b in bands),p['maximum_sampled_sidelobe_amplitude'],
           all(round(b['sampled_sidelobe_upper'],12)<=round(p['maximum_sampled_sidelobe_amplitude'],12) for b in bands),'REVISE_TAPER_GEOMETRY_OR_INTERFERENCE_DIRECTION'),
          ('WHITE_NOISE_GAIN_BOUND',min(b['white_noise_gain_lower'] for b in bands),p['minimum_white_noise_gain'],
           all(round(b['white_noise_gain_lower'],12)>=round(p['minimum_white_noise_gain'],12) for b in bands),'TRADE_DIRECTIVITY_AGAINST_CHANNEL_MISMATCH_ROBUSTNESS')]
    checks=[dict(id=key,actual=value,limit=limit,passed=passed,on_failure=action) for key,value,limit,passed,action in rows]
    return {'angles_deg':angles,'bands':bands,'output_noise_variance_ratio':noise,'output_noise_variance_upper_ratio':noise_upper,
        'worst_aperture_m':aperture,'worst_adjacent_spacing_m':largest_spacing,'alias_spacing_limit_m':alias_spacing,
        'fraunhofer_distance_m':fraunhofer,'required_source_range_m':range_required,'maximum_angular_gap_deg':gap,
        'checks':checks,'required_revisions':[r['on_failure'] for r in checks if not r['passed']],
        'disposition':'BOUNDED_BASELINE_ACCEPT' if all(r['passed'] for r in checks) else 'DESIGN_REVISION_REQUIRED',
        'physical_measurement_verified':False,'continuous_angle_verified':False,'speech_quality_verified':False,
        'counter_hypotheses':['Channel delay bias rather than incorrect taper','Gain or position mismatch rather than a steering algorithm defect',
                              'Unsampled spatial lobe rather than full-angle rejection'],
        'next_discriminating_experiment':'MEASURE_COMPLEX_CHANNEL_CALIBRATION_AND_DENSE_ANGULAR_RESPONSE_AT_FIXED_RANGE',
        'scope':'Supplied frequencies and hemisphere samples; fixed nominal true-time steering; independent interval bounds, not confidence intervals',
        'model_assumptions':['exp(j*omega*t); positive channel delay retards phase; positive angle advances signal at positive x',
            'Noise covariance sigma^2 I before nominal channel gains; WNG is not ambient SNR',
            'Far-field and half-wavelength guards are declared heuristics, not measured model validity',
            '12-decimal dimensionless comparison resolution is separate from supplied uncertainty'],
        'unresolved':['Actual array calibration and correlated or diffuse noise','Near-field, room reflections and full-angle/frequency behavior',
                      'Speech corpus, perceptual quality, physical and qualified Human acceptance']}
