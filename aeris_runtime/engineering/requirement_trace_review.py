"""Independent association traversal and exact interval assertion review."""
from fractions import Fraction
from .requirement_trace import validate,digest


def review(parameters,candidate):
    validate(parameters)
    p=parameters;rows=[];referenced=[];linked=0;current=0;bounded=0;total=0;complete=0
    for requirement in p['requirements']:
        assertions=[]
        for association in requirement['required_tests']:
            total+=1
            matching=[l for l in p['links'] if l['requirement_id']==requirement['id'] and l['test_id']==association['id']]
            row={'test_id':association['id'],'test_revision':association['revision'],'result_id':None,
                 'result_sha256':None,'interval':None,'interval_exact':None,'linked':bool(matching),
                 'current_semantics':False,'bounded_interval_passed':False,'reasons':[]}
            if not matching:
                row['reasons']=['MISSING_REQUIRED_ASSOCIATION'];assertions.append(row);continue
            link=matching[0];linked+=1
            record=next(r for r in p['results'] if r['id']==link['result_id'])
            definition=next(t for t in p['tests'] if t['id']==association['id'])
            supplied=record['payload'];referenced.append(record['id'])
            row.update(result_id=record['id'],result_sha256=record['sha256'])
            comparisons=[
                ('STALE_REQUIREMENT_REVISION',link['requirement_revision']==requirement['revision']),
                ('STALE_TEST_REVISION',all(v==association['revision'] for v in (link['test_revision'],definition['revision'],supplied['test_revision']))),
                ('RESULT_TEST_MISMATCH',supplied['test_id']==association['id']),
                ('LINK_RESULT_HASH_MISMATCH',link['result_sha256']==record['sha256']),
                ('CONFIGURATION_MISMATCH',supplied['configuration']==p['configuration'])]
            comparisons.extend((key.upper()+'_MISMATCH',requirement[key]==definition[key]==supplied[key]) for key in ('measurand','unit','reference'))
            comparisons.append(('RESULT_FAILED',supplied['status']=='COMPLETE'))
            row['reasons']=[reason for reason,passed in comparisons if not passed]
            row['current_semantics']=all(passed for _,passed in comparisons)
            if row['current_semantics']:
                current+=1
                center=Fraction(str(supplied['observed']));spread=Fraction(str(supplied['uncertainty']))
                minimum=Fraction(str(requirement['lower']));maximum=Fraction(str(requirement['upper']))
                row['interval_exact']=[str(center-spread),str(center+spread)]
                row['interval']=[float(center-spread),float(center+spread)]
                # Independent center-to-limit margins, not candidate endpoints.
                passed=center-minimum>=spread and maximum-center>=spread
                row['bounded_interval_passed']=passed
                if passed:bounded+=1
                else:row['reasons']=['OBSERVATION_OUTSIDE_LIMIT' if center<minimum or center>maximum else 'UNCERTAINTY_CROSSES_LIMIT']
            assertions.append(row)
        complete+=int(all(a['linked'] for a in assertions))
        rows.append({'requirement_id':requirement['id'],'requirement_revision':requirement['revision'],
                     'associations':assertions,'bounded_requirement_passed':all(a['bounded_interval_passed'] for a in assertions)})
    checks=[{'id':'REQUIRED_ASSOCIATION_COVERAGE','actual':linked,'limit':total,'passed':linked==total,'on_failure':'LINK_EVERY_DECLARED_REQUIRED_TEST'},
            {'id':'CURRENT_REVISION_AND_SEMANTICS','actual':current,'limit':total,'passed':current==total,'on_failure':'RECONCILE_VERSION_CONFIGURATION_AND_REFERENCE'},
            {'id':'BOUNDED_REQUIREMENT_INTERVALS','actual':bounded,'limit':total,'passed':bounded==total,'on_failure':'RESOLVE_MISSING_OR_UNSATISFIED_REQUIREMENT_INTERVAL'}]
    expected={'requirements_total':len(p['requirements']),'required_associations':total,'linked_associations':linked,
            'complete_requirements':complete,'current_associations':current,'bounded_associations':bounded,
            'requirements':rows,'unlinked_result_ids':sorted(r['id'] for r in p['results'] if r['id'] not in referenced),'checks':checks,
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
    # Exact serialized types distinguish False from 0 and do not tolerate changed
    # result digests or rational endpoint strings.
    same=isinstance(candidate,dict) and digest(candidate)==digest(expected)
    return {'decision':'BOUNDED_REVIEW_ACCEPT' if same else 'CHANGES_REQUIRED','expected':expected,
            'assertions_consistent':same,'human_approval':False,'role_l3_awarded':False,
            'review_scope':'Required association identity and supplied interval consistency; not physical/customer certification'}
