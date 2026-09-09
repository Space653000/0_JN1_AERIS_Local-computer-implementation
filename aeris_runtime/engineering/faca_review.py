"""Independent Decimal product/joint-entropy audit of supplied FACA models."""
import math
from decimal import Decimal, localcontext
from .faca import validate


def _same(left,right):
    if isinstance(left,bool) or isinstance(right,bool):return type(left) is type(right) and left==right
    if isinstance(left,(int,float)) and isinstance(right,(int,float)):
        return math.isfinite(left) and math.isfinite(right) and math.isclose(left,right,rel_tol=1e-10,abs_tol=1e-12)
    if isinstance(left,dict) and isinstance(right,dict):
        return set(left)==set(right) and all(_same(left[k],right[k]) for k in left)
    if isinstance(left,list) and isinstance(right,list):
        return len(left)==len(right) and all(_same(a,b) for a,b in zip(left,right))
    return type(left) is type(right) and left==right


def review(parameters,candidate):
    validate(parameters)
    p=parameters
    with localcontext() as context:
        context.prec=60
        weights={h['id']:Decimal(str(h['prior'])) for h in p['hypotheses']}
        for observation in p['observations']:
            for h in weights:
                factor=Decimal(str(observation['likelihoods'][h]))
                if 'experiment_id' in observation:
                    experiment=next(e for e in p['experiments'] if e['id']==observation['experiment_id'])
                    factor/=sum(Decimal(str(o['likelihoods'][h])) for o in experiment['outcomes'])
                weights[h]*=factor
        total=sum(weights.values())
        if not total:raise ValueError('every failure model contradicted')
        posterior={h:value/total for h,value in weights.items()}
        ln2=Decimal(2).ln()
        def entropy(values):return -sum(v*v.ln()/ln2 for v in values if v)
        prior_entropy=entropy(posterior.values())
        experiments=[]
        for experiment in p['experiments']:
            joint=[];outcome_marginals=[]
            columns={h:[Decimal(str(o['likelihoods'][h])) for o in experiment['outcomes']] for h in posterior}
            totals={h:sum(values) for h,values in columns.items()}
            for index in range(len(experiment['outcomes'])):
                cells=[prob*columns[h][index]/totals[h] for h,prob in posterior.items()]
                joint.extend(cells);outcome_marginals.append(sum(cells))
            gain=prior_entropy+entropy(outcome_marginals)-entropy(joint)
            if gain < Decimal('-1e-12'):raise ValueError('invalid negative information gain')
            gain=max(Decimal(0),gain)
            experiments.append({'id':experiment['id'],'expected_information_bits':float(gain),
                'information_per_cost':float(gain/Decimal(str(experiment['cost']))),
                'eligible':experiment['local_available'] and round(float(gain),12)>0})
        ranking=sorted(posterior,key=lambda h:(-round(float(posterior[h]),12),h))
        lead=float(posterior[ranking[0]]);margin=float(posterior[ranking[0]]-posterior[ranking[1]])
        separated=round(float(posterior[ranking[0]]),12)>round(float(posterior[ranking[1]]),12)
        eligible=sorted((e for e in experiments if e['eligible']),key=lambda e:(-round(e['information_per_cost'],12),e['id']))
        selected=eligible[0]['id'] if eligible else None
        checks=[{'id':'LEADING_MODEL_POSTERIOR','actual':lead,'limit':p['minimum_leading_posterior'],
                 'on_failure':'ACQUIRE_DISCRIMINATING_OBSERVATION',
                 'passed':round(lead,12)>=round(p['minimum_leading_posterior'],12)},
                {'id':'MODEL_SEPARATION_MARGIN','actual':margin,'limit':p['minimum_leading_margin'],
                 'on_failure':'SEPARATE_COMPETING_MECHANISMS',
                 'passed':separated and round(margin,12)>=round(p['minimum_leading_margin'],12)}]
        expected={'prior':{h['id']:h['prior'] for h in p['hypotheses']},
            'counter_hypotheses':[h['id']+': '+h['mechanism'] for h in p['hypotheses']],
            'posterior':{h:float(v) for h,v in posterior.items()},'ranking':ranking,
            'eliminated_hypotheses':[h for h,v in weights.items() if not v],
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
    accepted=_same(expected,candidate)
    return {'decision':'BOUNDED_REVIEW_ACCEPT' if accepted else 'CHANGES_REQUIRED',
            'expected':expected,'assertions_consistent':accepted,'human_approval':False,
            'review_scope':'Independent supplied-model probability and intervention ranking, not causal acceptance'}
