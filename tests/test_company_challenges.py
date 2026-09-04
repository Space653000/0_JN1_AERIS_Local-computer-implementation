import unittest
import copy
from unittest.mock import patch

from aeris_runtime.engineering import challenges
from aeris_runtime.engineering import factory
from aeris_runtime.engineering import catalog
from aeris_runtime import evidence, controlplane
from tests.engineering_test_support import isolated_engineering_state


class CompanyChallengeContractTests(unittest.TestCase):
    def test_unknown_numerical_oracle_is_not_zero_or_false(self):
        rule={'path':'noise','expected':None,'absolute_tolerance':0}
        for value,expected in ((None,True),(0,False),(False,False)):
            self.assertEqual(catalog.verify_checks({'noise':value},[rule])[0]['passed'],expected)

    def test_inventory_separates_implemented_challenges_from_remaining_software(self):
        items=challenges.inventory()
        self.assertEqual(len(items),8)
        self.assertEqual({x['id'] for x in items if x['implemented']},{'SPEAKER_FR','SPEAKER_POWER','MICROPHONE_NOISE','ARRAY_DOA','TWS_FIT','FAILURE_FACA'})

    def test_noop_and_requirement_relaxation_are_not_engineering_revisions(self):
        initial={'max_thd':5,'drive':2}
        challenges.validate_revision(initial,{'max_thd':5,'drive':1},{'max_thd':5},['drive'])
        for revised in (initial,{'max_thd':10,'drive':1},{'max_thd':5,'drive':1,'extra':1}):
            with self.subTest(revised=revised),self.assertRaises(ValueError):
                challenges.validate_revision(initial,revised,{'max_thd':5},['drive'])
        with self.assertRaises(ValueError): challenges.load_challenge('../../private')

    def test_role_scenario_reference_cannot_use_missing_or_invalid_input_case(self):
        definition=challenges.load_challenge('ARRAY_DOA')
        for case in ('MISSING','ARRAY-NEG-SILENCE'):
            with patch.object(challenges,'load_challenge',return_value={**definition,'initial_case_id':case}):
                with self.subTest(case=case),self.assertRaises(ValueError): challenges.run('ARRAY_DOA')

    def test_real_challenges_require_qualifications_and_reject_tampered_receipts(self):
        with isolated_engineering_state():
            blocked=challenges.run('SPEAKER_POWER')
            self.assertEqual(blocked['result'],'BLOCKED')
            self.assertEqual(controlplane.ControlStore().list_tasks(),[])
            with self.assertRaises(ValueError): challenges.run('REQUIREMENT_TRACEABILITY')
            for identifier in ('SPEAKER_FR','SPEAKER_POWER','MICROPHONE_NOISE','ARRAY_DOA','TWS_FIT','FAILURE_FACA'):
                result=challenges.run(identifier,prepare_qualifications=True)
                run_id=result['run_id']
                self.assertTrue(challenges.status(run_id)['valid'])
                self.assertEqual([s['report']['review']['decision'] for s in result['stages']],
                                 ['DESIGN_REVISION_REQUIRED','BOUNDED_REVIEW_ACCEPT'])
                self.assertFalse(result['role_l3_awarded'])
                self.assertFalse(result['memory']['memory_is_evidence'])
                self.assertEqual(len(controlplane.ControlStore().list_tasks(result['project_id'])),2)
                path=evidence.bundle_dir(run_id)/'processed/challenge.json'
                original=factory.read(path)
                for mutation in ('source','replay','stage','input','qualifications-array','report-array','review-array','root-array'):
                    altered=copy.deepcopy(original)
                    if mutation=='source': altered['bindings']['domain_source']='0'*64
                    elif mutation=='replay': altered['stages'][1]['reproduction']=altered['stages'][0]['reproduction']
                    elif mutation=='stage': altered['stages'][1]=altered['stages'][0]
                    elif mutation=='input': altered['inputs']['revised']['invented']=1
                    elif mutation=='qualifications-array': altered['qualifications']=list(altered['qualifications'])
                    elif mutation=='report-array': altered['stages'][0]['report']=[]
                    elif mutation=='review-array': altered['stages'][0]['report']['review']=[]
                    else: altered=[]
                    factory.write(path,altered)
                    evidence.seal_bundle(run_id,'negative test reseal')
                    with self.subTest(identifier=identifier,mutation=mutation):
                        self.assertFalse(challenges.status(run_id)['valid'])
                factory.write(path,original)
                evidence.seal_bundle(run_id,'restore test fixture')
                report_path=factory.STATE/'reports'/(result['stages'][0]['report']['workflow_id']+'.json')
                report=factory.read(report_path)
                factory.write(report_path,{**report,'human_approval':True})
                self.assertFalse(challenges.status(run_id)['valid'])
                factory.write(report_path,report)
                self.assertTrue(challenges.status(run_id)['valid'])
                child=evidence.bundle_dir(result['stages'][0]['report']['evidence_run_id'])/'processed/skill_result.json'
                factory.write(child,{})
                self.assertFalse(challenges.status(run_id)['valid'])

    def test_valid_other_attempt_and_missing_report_cannot_substitute(self):
        with isolated_engineering_state():
            first=challenges.run('TWS_FIT',prepare_qualifications=True)
            second=challenges.run('TWS_FIT')
            path=evidence.bundle_dir(first['run_id'])/'processed/challenge.json'
            original=factory.read(path)
            altered=copy.deepcopy(original)
            altered['stages'][1]=second['stages'][1]
            factory.write(path,altered)
            evidence.seal_bundle(first['run_id'],'wrong-attempt test reseal')
            self.assertTrue(challenges.status(second['run_id'])['valid'])
            self.assertFalse(challenges.status(first['run_id'])['valid'])
            # A mutable SQLite/report relabel must not transplant sealed evidence.
            transplanted=copy.deepcopy(original)
            item=copy.deepcopy(second['stages'][1])
            item['objective']=first['stages'][1]['objective']
            item['report']['project_id']=first['project_id']
            item['report_sha256']=catalog.digest(item['report'])
            with controlplane.ControlStore()._connect() as conn:
                conn.execute('UPDATE tasks SET project_id=?, title=? WHERE id=?',
                             (first['project_id'],item['objective'],item['report']['task_id']))
            factory.write(factory.STATE/'reports'/(item['report']['workflow_id']+'.json'),item['report'])
            transplanted['stages'][1]=item
            factory.write(path,transplanted)
            evidence.seal_bundle(first['run_id'],'relabelled wrong-attempt test reseal')
            self.assertFalse(challenges.status(first['run_id'])['valid'])
            factory.write(path,original)
            evidence.seal_bundle(first['run_id'],'restore test fixture')
            report_path=factory.STATE/'reports'/(first['stages'][0]['report']['workflow_id']+'.md')
            report_path.unlink()
            self.assertFalse(challenges.status(first['run_id'])['valid'])


if __name__=='__main__': unittest.main()
