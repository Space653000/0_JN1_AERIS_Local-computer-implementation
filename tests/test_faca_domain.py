"""Manually worked model probabilities are not physical causal evidence."""
import copy
import unittest
from aeris_runtime.engineering import faca
from aeris_runtime.engineering import faca_review


BASE = {
    'hypotheses': [
        {'id':'FIXTURE','mechanism':'Fixture ground loop','category':'TEST_SYSTEM','prior':0.5},
        {'id':'AMPLIFIER','mechanism':'Amplifier internal noise','category':'PRODUCT','prior':0.5}],
    'observations': [{'id':'OBS-1','source_record_id':'SYN-1','source_kind':'SYNTHETIC',
        'conditional_independence_assumed':True,'likelihoods':{'FIXTURE':0.5,'AMPLIFIER':0.5}}],
    'experiments': [{'id':'ISOLATE','intervention':'Isolate fixture ground path',
        'control':'Same amplifier, gain and load','cost':1,'risk':'R1','local_available':True,
        'outcomes':[{'id':'PERSISTS','likelihoods':{'FIXTURE':0.1,'AMPLIFIER':0.9}},
                    {'id':'CLEARS','likelihoods':{'FIXTURE':0.9,'AMPLIFIER':0.1}}]}],
    'minimum_leading_posterior':0.8,'minimum_leading_margin':0.5,
}


class FacaTests(unittest.TestCase):
    def test_normalization_roundoff_cannot_create_discriminating_information(self):
        p=copy.deepcopy(BASE);p['observations']=[];p['experiments'][0]['cost']=1e-12
        for outcome in p['experiments'][0]['outcomes']:
            outcome['likelihoods']={'FIXTURE':0.4999999999996,'AMPLIFIER':0.4999999999996}
        result=faca.analyze(p)
        self.assertEqual(result['experiments'][0]['expected_information_bits'],0)
        self.assertIsNone(result['selected_experiment_id'])
        self.assertEqual(faca_review.review(p,result)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_rounded_posterior_tie_cannot_pass_raw_margin(self):
        p=copy.deepcopy(BASE)
        p['hypotheses'][0]['prior']=0.4999999999996
        p['hypotheses'][1]['prior']=0.5000000000004
        p['minimum_leading_posterior']=0.5;p['minimum_leading_margin']=0
        result=faca.analyze(p)
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')
        self.assertEqual(faca_review.review(p,result)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_company_revision_origin_cannot_be_replaced_by_another_attempt(self):
        from tests.engineering_test_support import isolated_engineering_state
        from aeris_runtime.engineering import challenges,factory
        from aeris_runtime import evidence
        with isolated_engineering_state():
            first=challenges.run('FAILURE_FACA',prepare_qualifications=True)
            second=challenges.run('FAILURE_FACA')
            self.assertTrue(challenges.status(second['run_id'])['valid'])
            path=evidence.bundle_dir(second['run_id'])/'processed/challenge.json'
            original=factory.read(path)
            for bad in (first['revision_origin'],None,{**second['revision_origin'],'outcome_id':'CLEARS'}):
                factory.write(path,{**original,'revision_origin':bad})
                evidence.seal_bundle(second['run_id'],'test origin corruption')
                self.assertFalse(challenges.status(second['run_id'])['valid'])
            factory.write(path,original);evidence.seal_bundle(second['run_id'],'restore test origin')
            self.assertTrue(challenges.status(second['run_id'])['valid'])
            with self.assertRaises(ValueError):
                challenges._faca_origin(second['inputs'],first['stages'][0]['report'],second['run_id'])

    def test_role_specific_qualification_and_actual_reviewed_workflow(self):
        from tests.engineering_test_support import isolated_engineering_state
        from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
        from aeris_runtime.engineering.orchestration import run_role
        from aeris_runtime.engineering.domain_review import review_status
        from aeris_runtime import reproduction
        with isolated_engineering_state():
            for role in ('R094','R098'):
                result=RoleAcceptanceFactory().evaluate(role)
                self.assertTrue(result['execution_passed'],result)
                self.assertEqual(result['level'],'L2')
            report=run_role('R094','failure-hypothesis-experiment-baseline',BASE,
                            objective='Fixture versus amplifier discrimination',source_kind='SYNTHETIC',
                            context={'product':'Amplifier and test fixture'})
            self.assertEqual(report['review']['decision'],'DESIGN_REVISION_REQUIRED',report['review'])
            self.assertEqual([r['role_id'] for r in report['pod']['reviewers']],['R098'])
            self.assertTrue(review_status(report['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(report['evidence_run_id'])['result'],'PASS')

    def test_subresolution_hypothesis_difference_uses_same_ranking_tie_policy(self):
        p=copy.deepcopy(BASE)
        p['observations'][0]['likelihoods']={'FIXTURE':1.000000000000001e-100,'AMPLIFIER':1e-100}
        result=faca.analyze(p)
        self.assertEqual(result['ranking'],['AMPLIFIER','FIXTURE'])
        self.assertEqual(faca_review.review(p,result)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_weak_information_divided_by_small_cost_agrees_with_decimal_review(self):
        for epsilon in (1e-4,1e-5,1e-6):
            p=copy.deepcopy(BASE);p['experiments'][0]['cost']=1e-12
            p['experiments'][0]['outcomes']=[
                {'id':'PERSISTS','likelihoods':{'FIXTURE':0.5+epsilon,'AMPLIFIER':0.5-epsilon}},
                {'id':'CLEARS','likelihoods':{'FIXTURE':0.5-epsilon,'AMPLIFIER':0.5+epsilon}}]
            with self.subTest(epsilon=epsilon):
                self.assertEqual(faca_review.review(p,faca.analyze(p))['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_independent_decimal_review_challenges_model_and_causal_assertions(self):
        candidate=faca.analyze(BASE)
        self.assertEqual(faca_review.review(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        for field,value in (('posterior',{'FIXTURE':0.1,'AMPLIFIER':0.9}),
                            ('selected_experiment_id','DEPLOY'),('root_cause_verified',True),
                            ('next_discriminating_experiment','CLOSE_FACA'),('unresolved',[])):
            with self.subTest(field=field):
                self.assertEqual(faca_review.review(BASE,{**candidate,field:value})['decision'],'CHANGES_REQUIRED')

    def test_nearly_equal_experiment_scores_use_declared_resolution_then_id(self):
        p=copy.deepcopy(BASE)
        alternative=copy.deepcopy(p['experiments'][0]);alternative['id']='A-ALTERNATIVE';alternative['cost']=1+1e-14
        p['experiments'].append(alternative)
        result=faca.analyze(p)
        self.assertEqual(result['selected_experiment_id'],'A-ALTERNATIVE')
        self.assertEqual(faca_review.review(p,result)['decision'],'BOUNDED_REVIEW_ACCEPT')
        p['experiments'][1]['cost']=1+1e-6
        result=faca.analyze(p)
        self.assertEqual(result['selected_experiment_id'],'ISOLATE')
        self.assertEqual(faca_review.review(p,result)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_ambiguous_noise_selects_informative_controlled_experiment(self):
        result=faca.analyze(BASE)
        self.assertEqual(result['posterior'],{'FIXTURE':0.5,'AMPLIFIER':0.5})
        self.assertEqual(result['selected_experiment_id'],'ISOLATE')
        self.assertAlmostEqual(result['experiments'][0]['expected_information_bits'],0.5310044064107188)
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')
        self.assertFalse(result['root_cause_verified'])

    def test_hypothetical_result_updates_model_not_causal_closure(self):
        parameters=copy.deepcopy(BASE)
        parameters['observations'].append({'id':'OBS-2','source_record_id':'SYN-2','source_kind':'SYNTHETIC',
            'conditional_independence_assumed':True,'likelihoods':{'FIXTURE':0.1,'AMPLIFIER':0.9},
            'experiment_id':'ISOLATE','outcome_id':'PERSISTS'})
        result=faca.analyze(parameters)
        self.assertAlmostEqual(result['posterior']['AMPLIFIER'],0.9)
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertFalse(result['root_cause_verified'])
        self.assertFalse(result['recurrence_validated'])
        self.assertFalse(result['posterior_calibrated'])

    def test_duplicate_dependent_missing_and_inconsistent_rows_fail_closed(self):
        variants=[]
        p=copy.deepcopy(BASE);p['observations']*=2;variants.append(p)
        p=copy.deepcopy(BASE);p['observations'][0]['conditional_independence_assumed']=False;variants.append(p)
        p=copy.deepcopy(BASE);del p['observations'][0]['likelihoods']['FIXTURE'];variants.append(p)
        p=copy.deepcopy(BASE);p['observations'][0]['likelihoods']={'FIXTURE':0,'AMPLIFIER':0};variants.append(p)
        p=copy.deepcopy(BASE);p['experiments'][0]['outcomes'][0]['likelihoods']['FIXTURE']=0.4;variants.append(p)
        p=copy.deepcopy(BASE);p['hypotheses'][0]['prior']=True;variants.append(p)
        for p in variants:
            with self.subTest(p=p),self.assertRaises(ValueError):faca.analyze(p)

    def test_uninformative_or_unavailable_test_does_not_pretend_to_discriminate(self):
        p=copy.deepcopy(BASE)
        for outcome in p['experiments'][0]['outcomes']:
            outcome['likelihoods']={'FIXTURE':0.5,'AMPLIFIER':0.5}
        self.assertIsNone(faca.analyze(p)['selected_experiment_id'])

    def test_tied_models_remain_unresolved_even_with_zero_margin_policy(self):
        p=copy.deepcopy(BASE);p['minimum_leading_posterior']=0.5;p['minimum_leading_margin']=0
        self.assertEqual(faca.analyze(p)['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_log_space_retains_extremely_small_likelihood_products(self):
        p=copy.deepcopy(BASE)
        p['observations']=[{'id':f'O-{i}','source_record_id':f'S-{i}','source_kind':'SYNTHETIC',
            'conditional_independence_assumed':True,'likelihoods':{'FIXTURE':1e-100,'AMPLIFIER':2e-100}}
            for i in range(10)]
        self.assertAlmostEqual(faca.analyze(p)['posterior']['AMPLIFIER'],1024/1025)
        self.assertEqual(faca_review.review(p,faca.analyze(p))['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_revision_requires_append_only_selected_outcome_and_attempt_origin(self):
        first=faca.analyze(BASE)
        revised=copy.deepcopy(BASE)
        revised['observations'].append({'id':'O-2','source_record_id':'S-2','source_kind':'SYNTHETIC',
            'conditional_independence_assumed':True,'likelihoods':{'FIXTURE':0.1,'AMPLIFIER':0.9},
            'experiment_id':'ISOLATE','outcome_id':'PERSISTS'})
        receipt=faca.revision_receipt(BASE,revised,first,'ATTEMPT-1','EXECUTION-1')
        faca.verify_revision(BASE,revised,first,receipt,'ATTEMPT-1','EXECUTION-1')
        for field in ('attempt_id','initial_execution_id','experiment_sha256','outcome_id'):
            with self.subTest(field=field),self.assertRaises(ValueError):
                faca.verify_revision(BASE,revised,first,{**receipt,field:'FORGED'},'ATTEMPT-1','EXECUTION-1')
        changes=[]
        p=copy.deepcopy(revised);p['observations'][0]['likelihoods']['FIXTURE']=0.4;changes.append(p)
        p=copy.deepcopy(revised);p['observations'][-1]['likelihoods']['AMPLIFIER']=0.99;changes.append(p)
        p=copy.deepcopy(revised);p['experiments'][0]['cost']=2;changes.append(p)
        p=copy.deepcopy(revised);p['experiments'][0]['local_available']=False;changes.append(p)
        p=copy.deepcopy(revised);p['observations']*=2;changes.append(p)
        for p in changes:
            with self.subTest(p=p),self.assertRaises(ValueError):
                faca.revision_receipt(BASE,p,first,'ATTEMPT-1','EXECUTION-1')
        p=copy.deepcopy(BASE);p['experiments'][0]['local_available']=False
        self.assertIsNone(faca.analyze(p)['selected_experiment_id'])


if __name__=='__main__':unittest.main()
