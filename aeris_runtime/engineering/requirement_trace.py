"""Versioned ALL-association coverage; content identity is not authenticity."""
import hashlib
import json
import math
import re
from fractions import Fraction


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def _object(value, keys):
    if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError('exact trace object fields required')


def _text(value):
    if not isinstance(value,str) or not value.strip() or len(value)>256:raise ValueError('bounded nonempty trace identity required')


def _number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>1e12:
        raise ValueError('finite bounded observation/limit required')


def _array(value, minimum=0):
    if not isinstance(value,list) or not minimum<=len(value)<=256:raise ValueError('bounded trace rows required')


def _indexed(rows, minimum=0):
    _array(rows,minimum);result={}
    for row in rows:
        if not isinstance(row,dict):raise ValueError('object row required')
        _text(row.get('id'))
        if row['id'] in result:raise ValueError('duplicate trace row identity')
        result[row['id']]=row
    return result


def _configuration(value):
    _object(value,('product','revision'))
    for v in value.values():_text(v)


def validate(p):
    _object(p,('configuration','requirements','tests','results','links'))
    _configuration(p['configuration'])
    requirements=_indexed(p['requirements'],1);tests=_indexed(p['tests'],1);results=_indexed(p['results'])
    _array(p['links'])
    for requirement in requirements.values():
        _object(requirement,('id','revision','measurand','unit','reference','lower','upper','combination','required_tests'))
        for key in ('revision','measurand','unit','reference'):_text(requirement[key])
        _number(requirement['lower']);_number(requirement['upper'])
        if requirement['lower']>requirement['upper'] or requirement['combination']!='ALL':
            raise ValueError('ordered limits and explicit ALL combination required')
        expected=_indexed(requirement['required_tests'],1)
        for row in expected.values():
            _object(row,('id','revision'));_text(row['revision'])
            if row['id'] not in tests:raise ValueError('required test definition missing')
    for test in tests.values():
        _object(test,('id','revision','measurand','unit','reference'))
        for value in test.values():_text(value)
    source_ids=set()
    for result in results.values():
        _object(result,('id','payload','sha256'));payload=result['payload']
        _object(payload,('test_id','test_revision','configuration','measurand','unit','reference','observed','uncertainty','source_record_id','source_kind','status'))
        for key in ('test_id','test_revision','measurand','unit','reference','source_record_id'):_text(payload[key])
        _configuration(payload['configuration']);_number(payload['observed']);_number(payload['uncertainty'])
        if payload['uncertainty']<0:raise ValueError('nonnegative supplied uncertainty bound required')
        if payload['test_id'] not in tests:raise ValueError('result test definition missing')
        if payload['source_kind'] not in ('SYNTHETIC','SUPPLIED_UNVERIFIED') or payload['status'] not in ('COMPLETE','FAILED'):
            raise ValueError('cannot self-assert physical verification or unknown result status')
        if payload['source_record_id'] in source_ids:raise ValueError('duplicate source identity; reuse the same result explicitly')
        source_ids.add(payload['source_record_id'])
        if not isinstance(result['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',result['sha256']) or digest(payload)!=result['sha256']:
            raise ValueError('result content digest mismatch')
    associations=set()
    for link in p['links']:
        _object(link,('requirement_id','requirement_revision','test_id','test_revision','result_id','result_sha256'))
        for value in link.values():_text(value)
        if link['requirement_id'] not in requirements or link['test_id'] not in tests or link['result_id'] not in results:
            raise ValueError('dangling trace link')
        key=(link['requirement_id'],link['test_id'])
        if key in associations:raise ValueError('ambiguous duplicate association')
        associations.add(key)
        if link['test_id'] not in {t['id'] for t in requirements[link['requirement_id']]['required_tests']}:
            raise ValueError('link cannot invent a required association')
    return requirements,tests,results


def analyze(parameters):
    requirements,tests,results=validate(parameters)
    p=parameters;links={(l['requirement_id'],l['test_id']):l for l in p['links']}
    rows=[];complete=0;bounded=0;current=0;linked=0;required=0;used=set()
    for requirement in p['requirements']:
        associations=[]
        for expected in requirement['required_tests']:
            required+=1;link=links.get((requirement['id'],expected['id']));reasons=[]
            row={'test_id':expected['id'],'test_revision':expected['revision'],'result_id':None,
                 'result_sha256':None,'interval':None,'interval_exact':None,'linked':link is not None,'current_semantics':False,
                 'bounded_interval_passed':False,'reasons':reasons}
            if link is None:
                reasons.append('MISSING_REQUIRED_ASSOCIATION');associations.append(row);continue
            linked+=1;used.add(link['result_id']);test=tests[expected['id']];result=results[link['result_id']];payload=result['payload']
            row['result_id']=result['id'];row['result_sha256']=result['sha256']
            if link['requirement_revision']!=requirement['revision']:reasons.append('STALE_REQUIREMENT_REVISION')
            if link['test_revision']!=expected['revision'] or test['revision']!=expected['revision'] or payload['test_revision']!=expected['revision']:
                reasons.append('STALE_TEST_REVISION')
            if payload['test_id']!=expected['id']:reasons.append('RESULT_TEST_MISMATCH')
            if link['result_sha256']!=result['sha256']:reasons.append('LINK_RESULT_HASH_MISMATCH')
            if payload['configuration']!=p['configuration']:reasons.append('CONFIGURATION_MISMATCH')
            for key in ('measurand','unit','reference'):
                if requirement[key]!=test[key] or requirement[key]!=payload[key]:reasons.append(key.upper()+'_MISMATCH')
            if payload['status']!='COMPLETE':reasons.append('RESULT_FAILED')
            row['current_semantics']=not reasons
            if not reasons:
                current+=1
                # Exact rational input spelling; no precision context can erase
                # nonzero uncertainty. Float intervals are presentation only.
                observed=Fraction(str(payload['observed']));uncertainty=Fraction(str(payload['uncertainty']))
                low=observed-uncertainty;high=observed+uncertainty
                row['interval']=[float(low),float(high)]
                row['interval_exact']=[str(low),str(high)]
                if Fraction(str(requirement['lower']))<=low and high<=Fraction(str(requirement['upper'])):
                    row['bounded_interval_passed']=True;bounded+=1
                else:
                    reasons.append('OBSERVATION_OUTSIDE_LIMIT' if not Fraction(str(requirement['lower']))<=observed<=Fraction(str(requirement['upper'])) else 'UNCERTAINTY_CROSSES_LIMIT')
            associations.append(row)
        if all(a['linked'] for a in associations):complete+=1
        rows.append({'requirement_id':requirement['id'],'requirement_revision':requirement['revision'],
                     'associations':associations,'bounded_requirement_passed':all(a['bounded_interval_passed'] for a in associations)})
    checks=[{'id':'REQUIRED_ASSOCIATION_COVERAGE','actual':linked,'limit':required,'passed':linked==required,'on_failure':'LINK_EVERY_DECLARED_REQUIRED_TEST'},
            {'id':'CURRENT_REVISION_AND_SEMANTICS','actual':current,'limit':required,'passed':current==required,'on_failure':'RECONCILE_VERSION_CONFIGURATION_AND_REFERENCE'},
            {'id':'BOUNDED_REQUIREMENT_INTERVALS','actual':bounded,'limit':required,'passed':bounded==required,'on_failure':'RESOLVE_MISSING_OR_UNSATISFIED_REQUIREMENT_INTERVAL'}]
    return {'requirements_total':len(requirements),'required_associations':required,'linked_associations':linked,
            'complete_requirements':complete,'current_associations':current,'bounded_associations':bounded,
            'requirements':rows,'unlinked_result_ids':sorted(set(results)-used),'checks':checks,
            'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'real_evidence_count':0,'physical_measurement_verified':False,'source_authenticity_verified':False,
            'customer_approval':False,'counter_hypotheses':['Missing or stale linkage rather than a failing product',
                'Reference or configuration mismatch rather than acoustic drift'],
            'next_discriminating_experiment':'RECONCILE_EXACT_REQUIRED_ASSOCIATIONS_AND_CONFIGURATION',
            'model_assumptions':['ALL expected associations fixed independently of actual links',
                'Exact unit, measurand and reference identity; no inferred conversion',
                'Exact rational supplied bounds; float interval is presentation only, not measured statistical confidence'],
            'unresolved':['Source authenticity, calibration and physical acquisition','Qualified requirement and customer approval']}


def validate_revision(initial,revised):
    """Challenge revision is a new association, never a relaxed requirement."""
    validate(initial);validate(revised)
    for key in initial:
        if key!='links' and digest(initial[key])!=digest(revised[key]):
            raise ValueError('immutable requirement/test/result/configuration changed')
    if len(revised['links'])!=len(initial['links'])+1 or digest(revised['links'][:-1])!=digest(initial['links']):
        raise ValueError('append exactly one expected link without replacing previous links')
    return True
