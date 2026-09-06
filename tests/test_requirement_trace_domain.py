"""Expected associations are independent of supplied links."""
import copy
import hashlib
import json
import unittest
from aeris_runtime.engineering import requirement_trace
from aeris_runtime.engineering import requirement_trace_review


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


CONFIG={'product':'SYNTHETIC_SPEAKER','revision':'A'}
TESTS=[{'id':name,'revision':'1','measurand':'on_axis_level','unit':'dB','reference':'20uPa_1m_1Vrms'} for name in ('T-LOW','T-HIGH')]
RESULTS=[]
for test in TESTS:
    payload={'test_id':test['id'],'test_revision':test['revision'],'configuration':CONFIG,
             'measurand':test['measurand'],'unit':test['unit'],'reference':test['reference'],
             'observed':80,'uncertainty':1,'source_record_id':'SYN-'+test['id'],
             'source_kind':'SYNTHETIC','status':'COMPLETE'}
    RESULTS.append({'id':'RESULT-'+test['id'],'payload':payload,'sha256':digest(payload)})
BASE={'configuration':CONFIG,'requirements':[{'id':'FR','revision':'1','measurand':'on_axis_level','unit':'dB',
      'reference':'20uPa_1m_1Vrms','lower':78,'upper':82,'combination':'ALL',
      'required_tests':[{'id':test['id'],'revision':test['revision']} for test in TESTS]}],
      'tests':TESTS,'results':RESULTS,'links':[{'requirement_id':'FR','requirement_revision':'1',
      'test_id':test['id'],'test_revision':'1','result_id':result['id'],'result_sha256':result['sha256']}
      for test,result in zip(TESTS,RESULTS)]}


class RequirementTraceTests(unittest.TestCase):
    def test_challenge_seals_link_addition_to_same_attempt(self):
        from tests.engineering_test_support import isolated_engineering_state
        from aeris_runtime.engineering import challenges,factory
        from aeris_runtime import evidence
        with isolated_engineering_state():
            first=challenges.run('REQUIREMENT_TRACEABILITY',prepare_qualifications=True)
            second=challenges.run('REQUIREMENT_TRACEABILITY')
            self.assertTrue(challenges.status(second['run_id'])['valid'])
            path=evidence.bundle_dir(second['run_id'])/'processed/challenge.json';original=factory.read(path)
            for receipt in (first['revision_origin'],None,{**second['revision_origin'],'new_link_sha256':'0'*64}):
                factory.write(path,{**original,'revision_origin':receipt});evidence.seal_bundle(second['run_id'],'test trace origin corruption')
                self.assertFalse(challenges.status(second['run_id'])['valid'])
            factory.write(path,original);evidence.seal_bundle(second['run_id'],'restore trace receipt')
            with self.assertRaises(ValueError):
                challenges._trace_origin(second['inputs'],first['stages'][0]['report'],second['run_id'])

    def test_qualified_trace_role_runs_actual_workflow_and_reproduction(self):
        from tests.engineering_test_support import isolated_engineering_state
        from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
        from aeris_runtime.engineering.orchestration import run_role
        from aeris_runtime.engineering.domain_review import review_status
        from aeris_runtime import reproduction
        with isolated_engineering_state():
            for role in ('R097','R099'):
                result=RoleAcceptanceFactory().evaluate(role)
                self.assertTrue(result['execution_passed'],result)
                self.assertEqual(result['level'],'L2')
            report=run_role('R097','requirement-association-baseline',BASE,
                objective='Versioned FR required associations',source_kind='SYNTHETIC',context={'product':'SYNTHETIC_SPEAKER','transducer':'Speaker'})
            self.assertEqual(report['review']['decision'],'BOUNDED_REVIEW_ACCEPT',report['review'])
            self.assertEqual([r['role_id'] for r in report['pod']['reviewers']],['R099'])
            self.assertTrue(review_status(report['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(report['evidence_run_id'])['result'],'PASS')

    def test_independent_review_checks_denominators_revisions_and_entire_claim(self):
        candidate=requirement_trace.analyze(BASE)
        self.assertEqual(requirement_trace_review.review(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        for field,value in (('required_associations',1),('real_evidence_count',2),
                            ('source_authenticity_verified',True),('unresolved',[]),
                            ('next_discriminating_experiment','CERTIFY_CUSTOMER')):
            with self.subTest(field=field):
                self.assertEqual(requirement_trace_review.review(BASE,{**candidate,field:value})['decision'],'CHANGES_REQUIRED')

    def test_nonzero_tiny_uncertainty_never_disappears_into_zero_width_limit(self):
        p=copy.deepcopy(BASE);p['requirements'][0]['lower']=80;p['requirements'][0]['upper']=80
        for result,link in zip(p['results'],p['links']):
            result['payload']['uncertainty']=1e-30;result['sha256']=digest(result['payload']);link['result_sha256']=result['sha256']
        result=requirement_trace.analyze(p)
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')
        row=result['requirements'][0]['associations'][0]
        self.assertIn('UNCERTAINTY_CROSSES_LIMIT',row['reasons'])
        self.assertNotEqual(row['interval_exact'][0],row['interval_exact'][1])

    def test_same_result_can_support_distinct_limits_only_with_matching_semantics(self):
        p=copy.deepcopy(BASE)
        second=copy.deepcopy(p['requirements'][0]);second['id']='FR-TIGHT';second['lower']=79;second['upper']=81
        p['requirements'].append(second)
        p['links'].extend([{**link,'requirement_id':'FR-TIGHT'} for link in list(p['links'])])
        result=requirement_trace.analyze(p)
        self.assertEqual(result['required_associations'],4)
        self.assertEqual(result['complete_requirements'],2)
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT')
        p['requirements'][1]['reference']='1Pa_10cm'
        result=requirement_trace.analyze(p)
        self.assertEqual(result['bounded_associations'],2)
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_stale_revision_cannot_be_hidden_by_current_result_flag(self):
        p=copy.deepcopy(BASE);p['links'][0]['requirement_revision']='0'
        result=requirement_trace.analyze(p)
        self.assertIn('STALE_REQUIREMENT_REVISION',result['requirements'][0]['associations'][0]['reasons'])
        self.assertEqual(result['current_associations'],1)

    def test_revision_only_appends_one_expected_link_without_altering_denominators(self):
        initial=copy.deepcopy(BASE);initial['links']=initial['links'][:1]
        requirement_trace.validate_revision(initial,BASE)
        variants=[]
        p=copy.deepcopy(BASE);p['requirements'][0]['required_tests']=p['requirements'][0]['required_tests'][:1];p['links']=p['links'][:1];variants.append(p)
        p=copy.deepcopy(BASE);p['requirements'][0]['upper']=100;variants.append(p)
        p=copy.deepcopy(BASE);p['links'][0]['requirement_revision']='0';variants.append(p)
        p=copy.deepcopy(BASE);p['results'][0]['payload']['observed']=79;p['results'][0]['sha256']=digest(p['results'][0]['payload']);p['links'][0]['result_sha256']=p['results'][0]['sha256'];variants.append(p)
        for p in variants:
            with self.subTest(p=p),self.assertRaises(ValueError):requirement_trace.validate_revision(initial,p)

    def test_one_of_two_required_associations_is_not_complete_coverage(self):
        p=copy.deepcopy(BASE);p['links']=p['links'][:1]
        result=requirement_trace.analyze(p)
        self.assertEqual(result['required_associations'],2)
        self.assertEqual(result['linked_associations'],1)
        self.assertEqual(result['complete_requirements'],0)
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_complete_synthetic_links_do_not_verify_physical_measurement(self):
        result=requirement_trace.analyze(BASE)
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertEqual(result['real_evidence_count'],0)
        self.assertFalse(result['physical_measurement_verified'])
        self.assertFalse(result['source_authenticity_verified'])

    def test_same_unit_different_reference_or_configuration_fails_semantic_match(self):
        for key,value in (('reference','1Pa_10cm'),('measurand','distortion_level'),
                          ('configuration',{'product':'SYNTHETIC_SPEAKER','revision':'B'})):
            p=copy.deepcopy(BASE);p['results'][0]['payload'][key]=value
            p['results'][0]['sha256']=digest(p['results'][0]['payload'])
            p['links'][0]['result_sha256']=p['results'][0]['sha256']
            with self.subTest(key=key):
                self.assertEqual(requirement_trace.analyze(p)['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_interval_boundary_and_real_exceedance(self):
        p=copy.deepcopy(BASE);p['requirements'][0]['lower']=79;p['requirements'][0]['upper']=81
        self.assertEqual(requirement_trace.analyze(p)['disposition'],'BOUNDED_BASELINE_ACCEPT')
        p['requirements'][0]['upper']=80.999
        self.assertEqual(requirement_trace.analyze(p)['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_hash_mutation_empty_requirements_duplicate_and_dangling_link_rejected(self):
        variants=[]
        p=copy.deepcopy(BASE);p['results'][0]['payload']['observed']=100;variants.append(p)
        p=copy.deepcopy(BASE);p['requirements']=[];variants.append(p)
        p=copy.deepcopy(BASE);p['links']*=2;variants.append(p)
        p=copy.deepcopy(BASE);p['links'][0]['test_id']='UNKNOWN';variants.append(p)
        for p in variants:
            with self.subTest(p=p),self.assertRaises(ValueError):requirement_trace.analyze(p)


if __name__=='__main__':unittest.main()
