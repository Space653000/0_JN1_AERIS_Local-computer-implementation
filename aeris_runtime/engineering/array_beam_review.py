"""R034 independent real-vector recomputation of sampled ULA assertions."""
import math


def review(p,candidate):
    # Full scalar/vector schema is checked at the public review envelope.
    if p['model']!='FAR_FIELD_ULA_TRUE_TIME_DELAY' or p['noise_model']!='UNCORRELATED_EQUAL_VARIANCE_BEFORE_GAIN':
        raise ValueError('unsupported propagation/noise covariance')
    n=len(p['weights']);z=sum(p['weights'])
    if z<=0 or any(len(p[k])!=n for k in ('channel_gains','channel_delays_s','gain_bounds','delay_bounds_s','position_bounds_m')):
        raise ValueError('nonzero matched elements required')
    # Common positive taper scale has no physical meaning. Normalize before
    # multiplying or squaring, including subnormal but valid input weights.
    normalized=[a/z for a in p['weights']]
    if any(e>=g for e,g in zip(p['gain_bounds'],p['channel_gains'])) or any(e>=p['spacing_m']/2 for e in p['position_bounds_m']):
        raise ValueError('gain/position bounds violate model')
    for key in ('angles_deg','frequencies_hz'):
        if any(b<=a for a,b in zip(p[key],p[key][1:])):raise ValueError('ordered samples required')
    if p['angles_deg'][0]!=-90 or p['angles_deg'][-1]!=90:raise ValueError('incomplete declared hemisphere')
    grid=sorted(set(p['angles_deg']+[p['steering_deg']]))
    off=[i for i,a in enumerate(grid) if abs(a-p['steering_deg'])>p['main_lobe_exclusion_deg']]
    if not off:raise ValueError('no sidelobe samples')
    # Real in-phase/quadrature projection, not the executor's complex exponential.
    def amplitude(f,theta):
        radians=math.pi/180;wave=2*math.pi*f/p['sound_speed_m_s']
        phases=[wave*i*p['spacing_m']*(math.sin(theta*radians)-math.sin(p['steering_deg']*radians))
                -2*math.pi*f*delay for i,delay in enumerate(p['channel_delays_s'])]
        real=sum(a*g*math.cos(phi) for a,g,phi in zip(normalized,p['channel_gains'],phases))
        imag=sum(a*g*math.sin(phi) for a,g,phi in zip(normalized,p['channel_gains'],phases))
        center=math.sqrt(real*real+imag*imag)
        radius=0
        for a,g,ge,de,pe in zip(normalized,p['channel_gains'],p['gain_bounds'],p['delay_bounds_s'],p['position_bounds_m']):
            halfphase=math.pi*f*(pe*abs(math.sin(theta*radians))/p['sound_speed_m_s']+de)
            radius+=a*(ge+2*g*math.sin(min(halfphase,math.pi/2)))
        return center,max(0,center-radius),center+radius
    variance=sum(a*a*g*g for a,g in zip(normalized,p['channel_gains']))
    variance_upper=sum(a*a*(g+e)*(g+e) for a,g,e in zip(normalized,p['channel_gains'],p['gain_bounds']))
    bands=[]
    for frequency in p['frequencies_hz']:
        triples=[amplitude(frequency,a) for a in grid]
        target=triples[grid.index(p['steering_deg'])]
        bands.append({'frequency_hz':frequency,'sample_amplitudes':[v[0] for v in triples],
            'sample_lower':[v[1] for v in triples],'sample_upper':[v[2] for v in triples],
            'desired_amplitude':target[0],'desired_lower':target[1],'desired_upper':target[2],
            'sampled_sidelobe_upper':max(triples[i][2] for i in off),
            'white_noise_gain':target[0]*target[0]/variance,'white_noise_gain_lower':target[1]*target[1]/variance_upper})
    d=(n-1)*p['spacing_m']+p['position_bounds_m'][0]+p['position_bounds_m'][-1]
    spacing=max(p['spacing_m']+a+b for a,b in zip(p['position_bounds_m'],p['position_bounds_m'][1:]))
    limit=p['sound_speed_m_s']/p['frequencies_hz'][-1]/2
    fresnel=2*d*d*p['frequencies_hz'][-1]/p['sound_speed_m_s']
    distance=max(d*p['minimum_range_aperture_ratio'],fresnel*p['minimum_fraunhofer_ratio'])
    gap=max(b-a for a,b in zip(grid,grid[1:]))
    desired=min(v['desired_lower'] for v in bands);side=max(v['sampled_sidelobe_upper'] for v in bands)
    wng=min(v['white_noise_gain_lower'] for v in bands)
    rows=[('SPATIAL_SAMPLING_GUARD',spacing,limit,spacing<=limit,'REDUCE_SPACING_OR_DECLARED_BAND'),
        ('FAR_FIELD_HEURISTIC',p['source_range_m'],distance,p['source_range_m']>=distance,'USE_NEAR_FIELD_PROPAGATION_OR_INCREASE_RANGE'),
        ('ANGULAR_SAMPLING',gap,p['maximum_grid_gap_deg'],gap<=p['maximum_grid_gap_deg'],'REFINE_ANGULAR_GRID_WITHOUT_CLAIMING_CONTINUOUS_COVERAGE'),
        ('DESIRED_GAIN_BOUND',desired,p['minimum_desired_amplitude'],round(desired,12)>=round(p['minimum_desired_amplitude'],12),'RECALIBRATE_CHANNEL_GAIN_DELAY_OR_REVISE_STEERING'),
        ('SAMPLED_SIDELOBE_BOUND',side,p['maximum_sampled_sidelobe_amplitude'],round(side,12)<=round(p['maximum_sampled_sidelobe_amplitude'],12),'REVISE_TAPER_GEOMETRY_OR_INTERFERENCE_DIRECTION'),
        ('WHITE_NOISE_GAIN_BOUND',wng,p['minimum_white_noise_gain'],round(wng,12)>=round(p['minimum_white_noise_gain'],12),'TRADE_DIRECTIVITY_AGAINST_CHANNEL_MISMATCH_ROBUSTNESS')]
    checks=[dict(id=key,actual=value,limit=bound,passed=passed,on_failure=action) for key,value,bound,passed,action in rows]
    expected={'angles_deg':grid,'bands':bands,'output_noise_variance_ratio':variance,'output_noise_variance_upper_ratio':variance_upper,
        'worst_aperture_m':d,'worst_adjacent_spacing_m':spacing,'alias_spacing_limit_m':limit,
        'fraunhofer_distance_m':fresnel,'required_source_range_m':distance,'maximum_angular_gap_deg':gap,
        'checks':checks,'required_revisions':[v['on_failure'] for v in checks if not v['passed']],
        'disposition':'BOUNDED_BASELINE_ACCEPT' if all(v['passed'] for v in checks) else 'DESIGN_REVISION_REQUIRED',
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
    if not isinstance(candidate,dict) or set(candidate)!=set(expected):raise ValueError('exact sampled ULA report required')
    from .domain_review import _same_assertion
    def same(actual,wanted):
        if isinstance(wanted,dict):return isinstance(actual,dict) and set(actual)==set(wanted) and all(same(actual[k],v) for k,v in wanted.items())
        if isinstance(wanted,list):return isinstance(actual,list) and len(actual)==len(wanted) and all(same(a,b) for a,b in zip(actual,wanted))
        return _same_assertion(actual,wanted)
    differences=[{'field':k,'asserted':candidate[k],'expected':v} for k,v in expected.items() if not same(candidate[k],v)]
    return {'domain':'microphone-array-pattern','decision':'CHANGES_REQUIRED' if differences else 'BOUNDED_REVIEW_ACCEPT',
        'disagreements':differences,'human_approval':False,'role_l3_awarded':False,
        'scope':'sampled pattern, mismatch and white-noise consistency only; no professional or physical acceptance'}
