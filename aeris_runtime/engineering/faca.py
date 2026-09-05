"""Bounded failure-model inference; supplied likelihoods never prove a cause."""
import math
import re
import hashlib
import json
from decimal import Decimal, localcontext

RESOLUTION=12


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def revision_receipt(initial, revised, first_values, attempt_id, initial_execution_id):
    """Semantic receipt only; caller must obtain first_values from sealed execution.

    Not evidence by itself: company status must bind IDs, verify the initial
    bundle's integrity and compare its sealed input/output with these arguments.
    """
    validate(initial);validate(revised)
    _identifier(attempt_id);_identifier(initial_execution_id)
    for key in initial:
        if key!='observations' and _digest(initial[key])!=_digest(revised[key]):
            raise ValueError('revision changed model, policy or experiment definition')
    old=initial['observations'];new=revised['observations']
    if len(new)!=len(old)+1 or _digest(new[:-1])!=_digest(old):
        raise ValueError('exactly one append-only observation required')
    if not isinstance(first_values,dict):raise ValueError('sealed first output required')
    selected=first_values.get('selected_experiment_id')
    experiments=[e for e in initial['experiments'] if e['id']==selected and e['local_available']]
    if len(experiments)!=1 or new[-1].get('experiment_id')!=selected:
        raise ValueError('revision must use first selected available experiment')
    row=new[-1]
    if row['source_kind']!='SYNTHETIC':raise ValueError('challenge outcome must remain explicitly hypothetical')
    outcomes=[o for o in experiments[0]['outcomes'] if o['id']==row.get('outcome_id')]
    if len(outcomes)!=1 or outcomes[0]['likelihoods']!=row['likelihoods']:
        raise ValueError('outcome likelihood does not match selected experiment')
    return {'attempt_id':attempt_id,'initial_execution_id':initial_execution_id,
            'initial_input_sha256':_digest(initial),'initial_values_sha256':_digest(first_values),
            'experiment_id':selected,'experiment_sha256':_digest(experiments[0]),
            'outcome_id':row['outcome_id'],'observation_sha256':_digest(row),
            'classification':'SYNTHETIC_REVISION_ORIGIN_NOT_PHYSICAL_EVIDENCE'}


def verify_revision(initial, revised, first_values, receipt, attempt_id, initial_execution_id):
    expected=revision_receipt(initial,revised,first_values,attempt_id,initial_execution_id)
    if not isinstance(receipt,dict) or _digest(receipt)!=_digest(expected):
        raise ValueError('revision origin does not match the current sealed attempt')
    return True


def _object(value, required, optional=()):
    if not isinstance(value,dict) or not set(required)<=set(value) or set(value)-set(required)-set(optional):
        raise ValueError('exact object contract required')


def _identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',value):
        raise ValueError('bounded identifier required')


def _text(value):
    if not isinstance(value,str) or not value.strip() or len(value)>2000:
        raise ValueError('nonempty bounded mechanism/intervention text required')


def _number(value, low=0, high=1):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError('finite model number outside bounds')


def _rows(value, minimum, maximum):
    if not isinstance(value,list) or not minimum<=len(value)<=maximum:
        raise ValueError('bounded row array required')
    identifiers=[]
    for row in value:
        if not isinstance(row,dict):raise ValueError('object row required')
        _identifier(row.get('id')); identifiers.append(row['id'])
    if len(set(identifiers))!=len(identifiers):raise ValueError('duplicate row ID')


def validate(p):
    _object(p,('hypotheses','observations','experiments','minimum_leading_posterior','minimum_leading_margin'))
    _rows(p['hypotheses'],2,16);_rows(p['observations'],0,64);_rows(p['experiments'],0,32)
    ids={h['id'] for h in p['hypotheses']}
    categories=set();mechanisms=set()
    for h in p['hypotheses']:
        _object(h,('id','mechanism','category','prior'));_text(h['mechanism']);_number(h['prior'])
        if h['prior']==0 or h['category'] not in ('PRODUCT','TEST_SYSTEM'):
            raise ValueError('positive prior and supported mechanism category required')
        mechanisms.add(h['mechanism'].strip().casefold());categories.add(h['category'])
    if len(mechanisms)!=len(ids) or categories!={'PRODUCT','TEST_SYSTEM'}:
        raise ValueError('distinct product and test-system counter-hypotheses required')
    if abs(math.fsum(h['prior'] for h in p['hypotheses'])-1)>1e-12:
        raise ValueError('priors must normalize to one')
    def likelihoods(row):
        values=row['likelihoods']
        if not isinstance(values,dict) or set(values)!=ids:raise ValueError('complete likelihood coverage required')
        for value in values.values():_number(value)
    sources=set()
    for row in p['observations']:
        _object(row,('id','source_record_id','source_kind','conditional_independence_assumed','likelihoods'),('experiment_id','outcome_id'))
        _identifier(row['source_record_id'])
        if row['source_record_id'] in sources:raise ValueError('source reused as independent observation')
        sources.add(row['source_record_id'])
        if row['source_kind'] not in ('SYNTHETIC','SUPPLIED_UNVERIFIED') or row['conditional_independence_assumed'] is not True:
            raise ValueError('unsupported provenance or dependence assumption')
        likelihoods(row)
        if ('experiment_id' in row)!=('outcome_id' in row):raise ValueError('experiment/outcome pair required')
    for experiment in p['experiments']:
        _object(experiment,('id','intervention','control','cost','risk','local_available','outcomes'))
        _text(experiment['intervention']);_text(experiment['control']);_number(experiment['cost'],1e-12,1e12)
        if experiment['risk'] not in ('R0','R1') or type(experiment['local_available']) is not bool:
            raise ValueError('bounded local experiment policy required')
        _rows(experiment['outcomes'],2,32)
        for outcome in experiment['outcomes']:
            _object(outcome,('id','likelihoods'));likelihoods(outcome)
        if any(abs(math.fsum(o['likelihoods'][h] for o in experiment['outcomes'])-1)>1e-12 for h in ids):
            raise ValueError('outcome probabilities must normalize for every hypothesis')
    for row in p['observations']:
        if 'experiment_id' not in row:continue
        candidates=[o for e in p['experiments'] if e['id']==row['experiment_id'] for o in e['outcomes'] if o['id']==row['outcome_id']]
        if len(candidates)!=1 or candidates[0]['likelihoods']!=row['likelihoods']:
            raise ValueError('declared outcome must match experiment table; not proof of execution')
    _number(p['minimum_leading_posterior']);_number(p['minimum_leading_margin'])


def _information(posterior, experiment):
    """60-digit conditional entropy prevents tiny gain/cost cancellation.

    Reviewer uses joint entropy and Decimal likelihood products independently.
    Input decimal spelling is the contract; final floats retain comparison at
    12 decimals, not a statistical uncertainty or calibrated confidence bound.
    """
    with localcontext() as context:
        context.prec=60
        weights={h:Decimal(str(v)) for h,v in posterior.items()}
        total=sum(weights.values());probabilities={h:v/total for h,v in weights.items()}
        outcome_totals={h:sum(Decimal(str(o['likelihoods'][h])) for o in experiment['outcomes']) for h in probabilities}
        def entropy(values):return -sum(v*v.ln()/Decimal(2).ln() for v in values if v)
        expected=Decimal(0)
        for outcome in experiment['outcomes']:
            joint=[v*Decimal(str(outcome['likelihoods'][h]))/outcome_totals[h] for h,v in probabilities.items()]
            mass=sum(joint)
            if mass:expected+=mass*entropy([v/mass for v in joint])
        gain=entropy(probabilities.values())-expected
        if gain < Decimal('-1e-12'):raise ValueError('negative information gain inconsistent with model')
        gain=max(Decimal(0),gain)
        return float(gain),float(gain/Decimal(str(experiment['cost'])))


def analyze(parameters):
    validate(parameters)
    p=parameters
    logs={}
    for h in p['hypotheses']:
        likelihoods=[]
        for observation in p['observations']:
            value=observation['likelihoods'][h['id']]
            if 'experiment_id' in observation:
                experiment=next(e for e in p['experiments'] if e['id']==observation['experiment_id'])
                value/=math.fsum(o['likelihoods'][h['id']] for o in experiment['outcomes'])
            likelihoods.append(value)
        logs[h['id']]=math.log(h['prior'])+math.fsum(math.log(v) for v in likelihoods) if all(v>0 for v in likelihoods) else -math.inf
    largest=max(logs.values())
    if largest==-math.inf:raise ValueError('all hypotheses inconsistent with supplied observations')
    weights={h:math.exp(v-largest) for h,v in logs.items()}
    total=math.fsum(weights.values());posterior={h:w/total for h,w in weights.items()}
    ranked=sorted(posterior,key=lambda h:(-round(posterior[h],RESOLUTION),h))
    leading=posterior[ranked[0]];margin=leading-posterior[ranked[1]]
    separated=round(posterior[ranked[0]],RESOLUTION)>round(posterior[ranked[1]],RESOLUTION)
    experiments=[]
    for experiment in p['experiments']:
        gain,score=_information(posterior,experiment)
        experiments.append({'id':experiment['id'],'expected_information_bits':gain,'information_per_cost':score,
                            'eligible':experiment['local_available'] and round(gain,RESOLUTION)>0})
    eligible=sorted((e for e in experiments if e['eligible']),key=lambda e:(-round(e['information_per_cost'],RESOLUTION),e['id']))
    selected=eligible[0]['id'] if eligible else None
    checks=[{'id':'LEADING_MODEL_POSTERIOR','actual':leading,'limit':p['minimum_leading_posterior'],
             'on_failure':'ACQUIRE_DISCRIMINATING_OBSERVATION',
             'passed':round(leading,RESOLUTION)>=round(p['minimum_leading_posterior'],RESOLUTION)},
            {'id':'MODEL_SEPARATION_MARGIN','actual':margin,'limit':p['minimum_leading_margin'],
             'on_failure':'SEPARATE_COMPETING_MECHANISMS',
             'passed':separated and round(margin,RESOLUTION)>=round(p['minimum_leading_margin'],RESOLUTION)}]
    return {'prior':{h['id']:h['prior'] for h in p['hypotheses']},'posterior':posterior,'ranking':ranked,
            'counter_hypotheses':[h['id']+': '+h['mechanism'] for h in p['hypotheses']],
            'eliminated_hypotheses':[h for h,v in logs.items() if v==-math.inf],
            'experiments':experiments,'selected_experiment_id':selected,'checks':checks,
            'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'next_discriminating_experiment':selected or 'DEFINE_INFORMATIVE_CONTROLLED_EXPERIMENT',
            'root_cause_verified':False,'recurrence_validated':False,'posterior_calibrated':False,
            'physical_measurement_verified':False,
            'model_assumptions':['Supplied uncalibrated likelihoods and priors','Conditional independence is declared, not verified',
                                 'Information-gain ranking is model-derived; no experiment executed'],
            'unresolved':['Unmodeled mechanisms and dependent observations','Physical intervention and recurrence validation',
                          'Qualified domain Human causal approval']}
