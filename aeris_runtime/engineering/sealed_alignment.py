"""Ideal sealed-box T/S alignment with analytic independent-bound extrema."""
import math

FIELDS={
    'fs_hz':(0.1,10000),'fs_lower_hz':(0.1,10000),'fs_upper_hz':(0.1,10000),
    'qts':(0.01,5),'qts_lower':(0.01,5),'qts_upper':(0.01,5),
    'vas_m3':(1e-9,100),'vas_lower_m3':(1e-9,100),'vas_upper_m3':(1e-9,100),
    'box_m3':(1e-9,100),'box_lower_m3':(1e-9,100),'box_upper_m3':(1e-9,100),
    'maximum_f3_hz':(0.1,20000),'minimum_qtc':(0.01,20),'maximum_qtc':(0.01,20),
    'maximum_box_m3':(1e-9,100),'largest_dimension_m':(1e-6,100),'analysis_max_hz':(0.1,200000),
    'sound_speed_lower_m_s':(100,1000),'maximum_dimension_wavelength_ratio':(1e-6,1),
}


def validate(p):
    if not isinstance(p,dict) or set(p)!=set(FIELDS)|{'model'} or p['model']!='IDEAL_SEALED_SMALL_SIGNAL':
        raise ValueError('exact ideal sealed small-signal SI contract required')
    for key,(low,high) in FIELDS.items():
        value=p[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
            raise ValueError('finite declared parameter bounds required: '+key)
    for nominal,low,high in (('fs_hz','fs_lower_hz','fs_upper_hz'),('qts','qts_lower','qts_upper'),
                             ('vas_m3','vas_lower_m3','vas_upper_m3'),('box_m3','box_lower_m3','box_upper_m3')):
        if not p[low]<=p[nominal]<=p[high]:raise ValueError('nominal must lie inside independent supplied bounds')
    if p['minimum_qtc']>p['maximum_qtc']:raise ValueError('ordered Qtc policy required')


def _f3(fs,qts,alpha):
    qtc=qts*math.sqrt(alpha);b=2-1/(qtc*qtc)
    discriminant=math.hypot(b,2)
    normalized_square=2/(discriminant+b) if b>=0 else (discriminant-b)/2
    return fs*math.sqrt(alpha*normalized_square)


def analyze(parameters):
    validate(parameters);p=parameters
    alpha=1+p['vas_m3']/p['box_m3']
    amin=1+p['vas_lower_m3']/p['box_upper_m3'];amax=1+p['vas_upper_m3']/p['box_lower_m3']
    fc=p['fs_hz']*math.sqrt(alpha);qtc=p['qts']*math.sqrt(alpha);f3=_f3(p['fs_hz'],p['qts'],alpha)
    fc_bounds=[p['fs_lower_hz']*math.sqrt(amin),p['fs_upper_hz']*math.sqrt(amax)]
    q_bounds=[p['qts_lower']*math.sqrt(amin),p['qts_upper']*math.sqrt(amax)]
    # F3 is increasing in Fs and decreasing in Qts. Alpha has an interior
    # minimum at 1/(2*Qts^2), never an interior maximum.
    candidates=[amin,amax];critical=1/(2*p['qts_upper']**2)
    if amin<=critical<=amax:candidates.append(critical)
    lower=min(_f3(p['fs_lower_hz'],p['qts_upper'],a) for a in candidates)
    upper=max(_f3(p['fs_upper_hz'],p['qts_lower'],a) for a in (amin,amax))
    geometry=p['largest_dimension_m']*p['analysis_max_hz']/p['sound_speed_lower_m_s']
    coverage=max(fc_bounds[1],upper)
    checks=[{'id':'F3_UPPER_BOUND','actual':upper,'limit':p['maximum_f3_hz'],
             'passed':round(upper,9)<=round(p['maximum_f3_hz'],9),'on_failure':'REVISE_SEALED_ALIGNMENT_WITH_PARAMETER_TOLERANCES'},
            {'id':'QTC_INTERVAL','actual':q_bounds,'limit':[p['minimum_qtc'],p['maximum_qtc']],
             'passed':round(q_bounds[0],12)>=round(p['minimum_qtc'],12) and round(q_bounds[1],12)<=round(p['maximum_qtc'],12),
             'on_failure':'REVISE_DAMPING_OR_EFFECTIVE_BOX_COMPLIANCE'},
            {'id':'EFFECTIVE_BOX_VOLUME','actual':p['box_upper_m3'],'limit':p['maximum_box_m3'],
             'passed':p['box_upper_m3']<=p['maximum_box_m3'],'on_failure':'RESOLVE_AVAILABLE_EFFECTIVE_VOLUME'},
            {'id':'ANALYSIS_FREQUENCY_COVERAGE','actual':p['analysis_max_hz'],'limit':coverage,
             'passed':round(p['analysis_max_hz'],9)>=round(coverage,9),'on_failure':'EXTEND_VALIDATED_ANALYSIS_RANGE_TO_ALIGNMENT_BOUNDS'},
            {'id':'LUMPED_GEOMETRY_VALIDITY','actual':geometry,'limit':p['maximum_dimension_wavelength_ratio'],
             'passed':round(geometry,12)<=round(p['maximum_dimension_wavelength_ratio'],12),
             'on_failure':'REDUCE_GEOMETRIC_SCALE_OR_USE_A_SPATIALLY_VALID_MODEL'}]
    return {'alpha':alpha,'alpha_interval':[amin,amax],'fc_hz':fc,'fc_interval_hz':fc_bounds,
            'qtc':qtc,'qtc_interval':q_bounds,'f3_hz':f3,'f3_interval_hz':[lower,upper],
            'dimension_wavelength_ratio':geometry,'required_analysis_max_hz':coverage,
            'checks':checks,'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'excursion_verified':False,'ported_alignment_verified':False,'physical_measurement_verified':False,
            'counter_hypotheses':['Enclosure leakage rather than T/S parameter drift','Amplifier voltage droop rather than sealed-box roll-off'],
            'next_discriminating_experiment':'MEASURE_SMALL_SIGNAL_IMPEDANCE_AND_SEALED_VOLUME_LEAKAGE_AT_FIXED_DRIVE',
            'model_assumptions':['Ideal sealed linear compliance; no port, leakage or large-signal terms',
                'Independent supplied bounds, not calibrated probability distributions',
                'F3 relative to mathematical asymptotic high-pass gain, not a measured flat high-frequency response',
                '9-decimal Hz and 12-decimal dimensionless comparison representation, separate from model uncertainty'],
            'unresolved':['Measured T/S, effective compliance and leakage','Excursion, thermal capacity and nonlinear distortion',
                          'Higher spatial modes, physical and qualified Human acceptance']}
