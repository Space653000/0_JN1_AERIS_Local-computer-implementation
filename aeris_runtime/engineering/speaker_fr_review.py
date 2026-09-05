"""R079 independent monotone interval/reference consistency challenges."""
import math
from .numerical_policy import db_at_least, db_at_most, cycles_at_least


def review(p, candidate):
    # Structural/numeric schema is checked by domain_review before this seam.
    if p['propagation_model'] != 'FREE_FIELD_FAR_FIELD' or p['drive_model'] != 'LINEAR_SMALL_SIGNAL_SAME_CONFIG_NO_LIMITER':
        raise ValueError('unsupported reference normalization assumption')
    f=p['frequency_hz']; n=len(f)
    if any(len(p[key]) != n for key in ('spl_db','lower_mask_db','upper_mask_db')) or any(b <= a for a,b in zip(f,f[1:])):
        raise ValueError('unmatched or unordered frequency/reference arrays')
    if (not p['distance_lower_m'] <= p['distance_m'] <= p['distance_upper_m']
            or not p['drive_lower_v'] <= p['drive_voltage_v'] <= p['drive_upper_v']
            or any(lo > hi for lo,hi in zip(p['lower_mask_db'],p['upper_mask_db']))):
        raise ValueError('invalid uncertainty/reference bounds')
    scale=p['reference_voltage_v']/p['reference_distance_m']
    nominal=[level+20*math.log10(scale*p['distance_m']/p['drive_voltage_v']) for level in p['spl_db']]
    lower=[level-p['level_bound_db']+20*math.log10(scale*p['distance_lower_m']/p['drive_upper_v']) for level in p['spl_db']]
    upper=[level+p['level_bound_db']+20*math.log10(scale*p['distance_upper_m']/p['drive_lower_v']) for level in p['spl_db']]
    valid=[cycles_at_least(frequency*p['gate_seconds'],p['minimum_cycles']) for frequency in f]
    central=[db_at_least(value,lo) and db_at_most(value,hi) for value,lo,hi in zip(nominal,p['lower_mask_db'],p['upper_mask_db'])]
    covered=[db_at_least(left,lo) and db_at_most(right,hi) for left,right,lo,hi in zip(lower,upper,p['lower_mask_db'],p['upper_mask_db'])]
    decisions=[]
    for index in range(n):
        if not valid[index]: decision='INSUFFICIENT_MEASUREMENT_VALIDITY'
        elif not central[index]: decision='RESPONSE_OUTSIDE_SAMPLED_LIMITS'
        elif not covered[index]: decision='UNCERTAINTY_CROSSING'
        else: decision='WITHIN_SAMPLED_ENVELOPE'
        decisions.append(decision)
    checks=[{'id':'WINDOW_VALIDITY','passed':all(valid),'on_failure':'EXTEND_WINDOW_OR_REVISE_MEASUREMENT_METHOD'},
            {'id':'SAMPLED_INTERVAL_MASK','passed':all(covered),'on_failure':'RESOLVE_REFERENCE_UNCERTAINTY_OR_SAMPLED_RESPONSE'}]
    expected={'normalized_spl_db':nominal,'lower_interval_db':lower,'upper_interval_db':upper,
              'sample_decisions':decisions,'checks':checks,
              'full_band_conformance_verified':False,'linearity_measured':False,'calibration_verified':False,
              'physical_measurement_verified':False,
              'counter_hypotheses':['time-window truncation rather than product bass deficit',
                                    'distance or drive-reference mismatch rather than response change',
                                    'fixture or room contribution rather than transducer response']}
    expected.update(
        normalization_offset_db=20*math.log10(scale*p['distance_m']/p['drive_voltage_v']),
        observable_cycles=[frequency*p['gate_seconds'] for frequency in f],
        disposition='BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
        required_revisions=[c['on_failure'] for c in checks if not c['passed']],
        next_discriminating_experiment=('EXTEND_VALID_WINDOW_OR_USE_A_DIFFERENT_MEASUREMENT_METHOD' if not all(valid) else
                'RECHECK_DISTANCE_DRIVE_AND_LEVEL_UNCERTAINTY' if all(central) and not all(covered) else
                'REPEAT_MATCHED_FIXTURE_AND_REFERENCE_BEFORE_ATTRIBUTING_RESPONSE_TO_PRODUCT'),
        model_assumptions=['FREE_FIELD_FAR_FIELD','LINEAR_SMALL_SIGNAL_SAME_CONFIG_NO_LIMITER',
            'level bound excludes separately propagated distance and voltage bounds',
            'reference distance and voltage are exact target coordinates',
            'cycle threshold is a declared validity heuristic, not a universal accuracy guarantee'],
        scope='Supplied frequency samples only; no interpolation, full-band or physical conformance',
        unresolved=['actual calibrated acquisition and environment','unobserved frequencies and spatial response',
                    'actual small-signal validity and qualified Human review'])
    if not isinstance(candidate,dict) or set(candidate) != set(expected):
        raise ValueError('exact FR reference assertions required')
    from .domain_review import _same_assertion
    differences=[{'field':key,'asserted':candidate[key],'expected':value} for key,value in expected.items()
                 if not _same_assertion(candidate[key],value)]
    return {'domain':'speaker-fr-uncertainty','decision':'CHANGES_REQUIRED' if differences else 'BOUNDED_REVIEW_ACCEPT',
            'disagreements':differences,'observations':{'interval_scope':'monotone worst-case bounds, not confidence interval',
            'unresolved':'Actual calibration, linearity, room and unobserved frequencies'},
            'human_approval':False,'role_l3_awarded':False,'scope':'bounded reference/uncertainty report consistency only'}
