"""Supplied speaker FR references, bounded intervals and sampled validity only."""
import math
from .numerical_policy import db_at_least, db_at_most, cycles_at_least

ARRAY_FIELDS = {'frequency_hz', 'spl_db', 'lower_mask_db', 'upper_mask_db'}
SCALARS = {
    'distance_m': (1e-4,1000), 'distance_lower_m': (1e-4,1000), 'distance_upper_m': (1e-4,1000),
    'reference_distance_m': (1e-4,1000), 'drive_voltage_v': (1e-6,1000),
    'drive_lower_v': (1e-6,1000), 'drive_upper_v': (1e-6,1000), 'reference_voltage_v': (1e-6,1000),
    'level_bound_db': (0,60), 'gate_seconds': (1e-6,100), 'minimum_cycles': (2,100),
}
MODELS = {'propagation_model':'FREE_FIELD_FAR_FIELD',
          'drive_model':'LINEAR_SMALL_SIGNAL_SAME_CONFIG_NO_LIMITER'}


def _number(value, low, high):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('finite declared-unit number outside bounded applicability')


def validate(p):
    if not isinstance(p,dict) or set(p) != ARRAY_FIELDS | set(SCALARS) | set(MODELS):
        raise ValueError('exact speaker FR reference fields required')
    for key, bounds in SCALARS.items():
        _number(p[key],*bounds)
    for key, model in MODELS.items():
        if p[key] != model:
            raise ValueError('unsupported propagation or drive model assumption')
    for key in ARRAY_FIELDS:
        array=p[key]
        if not isinstance(array,list) or not 3 <= len(array) <= 1024:
            raise ValueError('3..1024 supplied frequency samples required')
        for value in array:
            _number(value,1 if key=='frequency_hz' else -120,100000 if key=='frequency_hz' else 200)
    n=len(p['frequency_hz'])
    if any(len(p[key]) != n for key in ARRAY_FIELDS):
        raise ValueError('sample and requirement arrays must align exactly')
    if any(b <= a for a,b in zip(p['frequency_hz'],p['frequency_hz'][1:])):
        raise ValueError('strictly increasing unique frequency required')
    if any(a > b for a,b in zip(p['lower_mask_db'],p['upper_mask_db'])):
        raise ValueError('inverted requirement envelope')
    if not p['distance_lower_m'] <= p['distance_m'] <= p['distance_upper_m'] or not p['drive_lower_v'] <= p['drive_voltage_v'] <= p['drive_upper_v']:
        raise ValueError('positive reference bounds must contain nominal values')


def analyze(p):
    validate(p)
    def offset(distance,voltage):
        return 20*math.log10(distance/p['reference_distance_m']) + 20*math.log10(p['reference_voltage_v']/voltage)
    nominal_offset=offset(p['distance_m'],p['drive_voltage_v'])
    low_offset=offset(p['distance_lower_m'],p['drive_upper_v'])-p['level_bound_db']
    high_offset=offset(p['distance_upper_m'],p['drive_lower_v'])+p['level_bound_db']
    nominal=[v+nominal_offset for v in p['spl_db']]
    lower=[v+low_offset for v in p['spl_db']]
    upper=[v+high_offset for v in p['spl_db']]
    cycles=[f*p['gate_seconds'] for f in p['frequency_hz']]
    valid=[cycles_at_least(c,p['minimum_cycles']) for c in cycles]
    nominal_pass=[db_at_least(v,lo) and db_at_most(v,hi) for v,lo,hi in zip(nominal,p['lower_mask_db'],p['upper_mask_db'])]
    robust=[db_at_least(lo,limit_lo) and db_at_most(hi,limit_hi) for lo,hi,limit_lo,limit_hi in zip(lower,upper,p['lower_mask_db'],p['upper_mask_db'])]
    decisions=['INSUFFICIENT_MEASUREMENT_VALIDITY' if not good else 'RESPONSE_OUTSIDE_SAMPLED_LIMITS' if not central else
               'UNCERTAINTY_CROSSING' if not bounded else 'WITHIN_SAMPLED_ENVELOPE'
               for good,central,bounded in zip(valid,nominal_pass,robust)]
    checks=[{'id':'WINDOW_VALIDITY','passed':all(valid),'on_failure':'EXTEND_WINDOW_OR_REVISE_MEASUREMENT_METHOD'},
            {'id':'SAMPLED_INTERVAL_MASK','passed':all(robust),'on_failure':'RESOLVE_REFERENCE_UNCERTAINTY_OR_SAMPLED_RESPONSE'}]
    experiment=('EXTEND_VALID_WINDOW_OR_USE_A_DIFFERENT_MEASUREMENT_METHOD' if not all(valid) else
                'RECHECK_DISTANCE_DRIVE_AND_LEVEL_UNCERTAINTY' if all(nominal_pass) and not all(robust) else
                'REPEAT_MATCHED_FIXTURE_AND_REFERENCE_BEFORE_ATTRIBUTING_RESPONSE_TO_PRODUCT')
    return {'normalized_spl_db':nominal,'lower_interval_db':lower,'upper_interval_db':upper,
            'normalization_offset_db':nominal_offset,'observable_cycles':cycles,'sample_decisions':decisions,
            'checks':checks,'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'next_discriminating_experiment':experiment,
            'counter_hypotheses':['time-window truncation rather than product bass deficit',
                                  'distance or drive-reference mismatch rather than response change',
                                  'fixture or room contribution rather than transducer response'],
            'model_assumptions':[MODELS['propagation_model'],MODELS['drive_model'],
                                 'level bound excludes separately propagated distance and voltage bounds',
                                 'reference distance and voltage are exact target coordinates',
                                 'cycle threshold is a declared validity heuristic, not a universal accuracy guarantee'],
            'scope':'Supplied frequency samples only; no interpolation, full-band or physical conformance',
            'full_band_conformance_verified':False,'linearity_measured':False,'calibration_verified':False,
            'unresolved':['actual calibrated acquisition and environment','unobserved frequencies and spatial response',
                          'actual small-signal validity and qualified Human review']}
