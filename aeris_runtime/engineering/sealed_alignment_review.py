"""Independent high-precision transfer-polynomial and interval review for R021."""
from decimal import Decimal, localcontext


def review(p, candidate):
    # The public review envelope validates field ranges before this seam.
    if p['model'] != 'IDEAL_SEALED_SMALL_SIGNAL':
        raise ValueError('only ideal sealed linear compliance is supported')
    for nominal, lower, upper in (('fs_hz','fs_lower_hz','fs_upper_hz'),
            ('qts','qts_lower','qts_upper'),('vas_m3','vas_lower_m3','vas_upper_m3'),
            ('box_m3','box_lower_m3','box_upper_m3')):
        if not p[lower] <= p[nominal] <= p[upper]:
            raise ValueError('inconsistent supplied independent bounds')
    if p['minimum_qtc'] > p['maximum_qtc']:
        raise ValueError('reversed damping limits')
    with localcontext() as ctx:
        ctx.prec = 60
        d = {key:Decimal(str(value)) for key,value in p.items() if key != 'model'}
        # Solve in (F3/Fs)^2 rather than the executor's normalized Fc equation.
        def root(fs, q, a):
            b = 2*a - 1/(q*q)
            y = (-b + (b*b + 4*a*a).sqrt())/2
            return fs*y.sqrt()
        a = 1+d['vas_m3']/d['box_m3']
        left = 1+d['vas_lower_m3']/d['box_upper_m3']
        right = 1+d['vas_upper_m3']/d['box_lower_m3']
        # Clamp the stationary minimizer to the interval; maxima are endpoints.
        minimizer = min(right,max(left,1/(2*d['qts_upper']**2)))
        lower = root(d['fs_lower_hz'],d['qts_upper'],minimizer)
        upper = max(root(d['fs_upper_hz'],d['qts_lower'],left),
                    root(d['fs_upper_hz'],d['qts_lower'],right))
        fc = d['fs_hz']*a.sqrt(); qtc = d['qts']*a.sqrt()
        fc_bounds = [d['fs_lower_hz']*left.sqrt(),d['fs_upper_hz']*right.sqrt()]
        q_bounds = [d['qts_lower']*left.sqrt(),d['qts_upper']*right.sqrt()]
        ratio = d['largest_dimension_m']*d['analysis_max_hz']/d['sound_speed_lower_m_s']
        coverage = max(fc_bounds[1],upper)
        # Convert to the declared output representation before inclusive policy.
        f3 = float(upper); qb = list(map(float,q_bounds)); geom = float(ratio)
        required = float(coverage)
        rows = [
            ('F3_UPPER_BOUND',f3,p['maximum_f3_hz'],round(f3,9)<=round(p['maximum_f3_hz'],9),
             'REVISE_SEALED_ALIGNMENT_WITH_PARAMETER_TOLERANCES'),
            ('QTC_INTERVAL',qb,[p['minimum_qtc'],p['maximum_qtc']],
             round(qb[0],12)>=round(p['minimum_qtc'],12) and round(qb[1],12)<=round(p['maximum_qtc'],12),
             'REVISE_DAMPING_OR_EFFECTIVE_BOX_COMPLIANCE'),
            ('EFFECTIVE_BOX_VOLUME',p['box_upper_m3'],p['maximum_box_m3'],p['box_upper_m3']<=p['maximum_box_m3'],
             'RESOLVE_AVAILABLE_EFFECTIVE_VOLUME'),
            ('ANALYSIS_FREQUENCY_COVERAGE',p['analysis_max_hz'],required,round(p['analysis_max_hz'],9)>=round(required,9),
             'EXTEND_VALIDATED_ANALYSIS_RANGE_TO_ALIGNMENT_BOUNDS'),
            ('LUMPED_GEOMETRY_VALIDITY',geom,p['maximum_dimension_wavelength_ratio'],
             round(geom,12)<=round(p['maximum_dimension_wavelength_ratio'],12),
             'REDUCE_GEOMETRIC_SCALE_OR_USE_A_SPATIALLY_VALID_MODEL')]
        checks = [dict(id=key,actual=value,limit=limit,passed=passed,on_failure=action)
                  for key,value,limit,passed,action in rows]
        expected = {'alpha':float(a),'alpha_interval':list(map(float,[left,right])),
            'fc_hz':float(fc),'fc_interval_hz':list(map(float,fc_bounds)),
            'qtc':float(qtc),'qtc_interval':qb,'f3_hz':float(root(d['fs_hz'],d['qts'],a)),
            'f3_interval_hz':list(map(float,[lower,upper])),
            'dimension_wavelength_ratio':geom,'required_analysis_max_hz':required,
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
    if not isinstance(candidate,dict) or set(candidate)!=set(expected):
        raise ValueError('exact sealed-alignment assertions required')
    from .domain_review import _same_assertion
    def same(actual,wanted):
        if isinstance(wanted,dict):
            return isinstance(actual,dict) and set(actual)==set(wanted) and all(same(actual[k],v) for k,v in wanted.items())
        if isinstance(wanted,list):
            return isinstance(actual,list) and len(actual)==len(wanted) and all(same(a,b) for a,b in zip(actual,wanted))
        return _same_assertion(actual,wanted)
    differences=[{'field':key,'asserted':candidate[key],'expected':value} for key,value in expected.items()
                 if not same(candidate[key],value)]
    return {'domain':'speaker-sealed-lumped','decision':'CHANGES_REQUIRED' if differences else 'BOUNDED_REVIEW_ACCEPT',
            'disagreements':differences,'observations':{'interval_scope':'independent supplied bounds, not calibrated distributions',
                'unresolved':'Actual impedance, leaks, nonlinear response and spatial modes'},
            'human_approval':False,'role_l3_awarded':False,'scope':'bounded sealed alignment/model-validity report consistency only'}
