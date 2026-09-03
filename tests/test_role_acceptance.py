"""Role-domain execution has its own questions, oracles and sealed evidence."""
import json
import copy
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import audit, evidence
from aeris_runtime.config import ROOT


class RoleAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack(); self.addCleanup(self.stack.close)
        base=ROOT/'.aeris/test-temp'; base.mkdir(parents=True,exist_ok=True)
        self.root=Path(self.stack.enter_context(tempfile.TemporaryDirectory(dir=base)))
        for module,name,value in ((evidence,'EVIDENCE_ROOT',self.root/'evidence'),
                (audit,'AUDIT_DIR',self.root/'audit'),(audit,'AUDIT_FILE',self.root/'audit/audit.jsonl'),
                (audit,'LOCK_FILE',self.root/'audit/.lock')):
            self.stack.enter_context(patch.object(module,name,value))

    def test_domain_cases_are_sealed_and_replayed_without_faking_independent_review(self):
        from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
        factory=RoleAcceptanceFactory(self.root/'acceptance')
        result=factory.evaluate('R048')
        self.assertEqual(result['case_count'],8)
        self.assertTrue(result['execution_passed'])
        self.assertEqual(result['level'],'L2')
        self.assertEqual(result['review_state'],'REVIEW_BLOCKED')
        self.assertFalse(result['role_l3_accepted'])
        self.assertFalse(result['physical_measurement_verified'])
        self.assertEqual(factory.status('R048')['level'],'L2')
        self.assertTrue(evidence.validate_bundle(result['run_id'])['valid'])
        self.assertEqual(factory.status('R047')['level'],'L1')
        index=self.root/'acceptance/R048.json'
        locator=json.loads(index.read_text()); locator.update(level='L4',role_l3_accepted=True)
        # Deliberate tamper fixture: mutable index labels must have no authority.
        index.write_text(json.dumps(locator),encoding='utf-8')
        self.assertEqual(factory.status('R048')['level'],'L2')
        record=evidence.bundle_dir(result['run_id'])/'processed/role-domain-execution.json'
        record.write_text('{}',encoding='utf-8')
        rejected=factory.status('R048')
        self.assertEqual(rejected['level'],'L1')
        self.assertFalse(rejected['execution_passed'])

    def test_bounded_review_roles_require_their_own_sealed_decision_suites(self):
        from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
        runner=RoleAcceptanceFactory(self.root/'acceptance')
        for role in ('R010','R075','R005','R029','R028','R030'):
            with self.subTest(role=role):
                result=runner.evaluate(role)
                self.assertTrue(result['execution_passed'])
                self.assertEqual(result['level'],'L2')
                self.assertGreaterEqual(result['case_count'],6)
                self.assertFalse(result['role_l3_accepted'])

    def test_microphone_reference_suite_proves_only_bounded_execution(self):
        from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
        result=RoleAcceptanceFactory(self.root/'acceptance').evaluate('R033')
        self.assertTrue(result['execution_passed'])
        self.assertEqual(result['case_count'],12)
        self.assertEqual(result['level'],'L2')
        self.assertFalse(result['role_l3_accepted'])

    def test_resealed_wrong_bindings_or_decision_results_cannot_grant_maturity(self):
        from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
        factory=RoleAcceptanceFactory(self.root/'acceptance')
        result=factory.evaluate('R048')
        original=json.loads((evidence.bundle_dir(result['run_id'])/'processed/role-domain-execution.json').read_text())
        mutations=[(name,'0'*64) for name in ('contract_sha256','artifacts_sha256','suite_sha256',
                   'method_source_sha256','engine_sha256','review_policy_sha256')]
        mutations.append(('role_id','R047'))
        for key,value in mutations:
            record=copy.deepcopy(original); record[key]=value
            with self.subTest(binding=key): self.assert_resealed_rejected(factory,record)
        record=copy.deepcopy(original); record['cases'][0]['output']['values']['anc_topology_candidate']='PASSIVE'
        self.assert_resealed_rejected(factory,record)
        record=copy.deepcopy(original); record['cases']=[c for c in record['cases'] if c['kind']!='boundary']
        self.assert_resealed_rejected(factory,record)
        record=copy.deepcopy(original); record['cases'][2]['passed']=False
        self.assert_resealed_rejected(factory,record)

    def test_speaker_suite_is_profession_specific_and_cross_seat_seal_is_rejected(self):
        from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
        factory=RoleAcceptanceFactory(self.root/'acceptance')
        speaker=factory.evaluate('R016'); tws=factory.evaluate('R048')
        self.assertEqual(speaker['level'],'L2')
        self.assertEqual(speaker['case_count'],8)
        self.assertEqual(speaker['review_state'],'REVIEW_BLOCKED')
        self.assertIn('Nonlinear/power',speaker['scope'])
        (self.root/'acceptance/R016.json').write_text(json.dumps({'run_id':tws['run_id']}),encoding='utf-8')
        rejected=factory.status('R016')
        self.assertEqual(rejected['level'],'L1')
        self.assertIn('mismatch',rejected['reason'])

    def test_matrix_exposes_only_evidenced_domain_skills_and_actual_case_count(self):
        from aeris_runtime.engineering import factory,role_acceptance,api
        with patch.object(role_acceptance,'STATE',self.root/'acceptance',create=True):
            result=role_acceptance.RoleAcceptanceFactory().evaluate('R048')
            matrix=factory.matrix(); row=next(r for r in matrix['roles'] if r['id']=='R048')
            self.assertEqual(row['level'],'L2')
            self.assertEqual(row['executable_skills'],['tws-fit-anc-call-baseline'])
            self.assertEqual(row['coverage']['role_domain_cases'],8)
            self.assertEqual(row['coverage']['role_acceptance'],0)
            self.assertEqual(matrix['total_role_golden_cases'],78)
            self.assertEqual(matrix['total_role_golden_suites'],9)
            fixture=api.get('/api/v1/capabilities/fixture/R048?skill=tws-fit-anc-call-baseline')
            self.assertEqual(fixture['source_kind'],'SYNTHETIC')
            self.assertEqual(fixture['fixture']['input']['feedback_delay_ms'],0.5)
            self.assertIn('tws-fit-anc-call-baseline',[s['skill_id'] for s in api.get('/api/v1/capabilities/skills')['skills']])

    def assert_resealed_rejected(self,factory,record):
        bundle=evidence.create_bundle('SYNTHETIC-MUTATION','test')
        path=evidence.bundle_dir(bundle['run_id'])/'processed/role-domain-execution.json'
        path.write_text(json.dumps(record),encoding='utf-8')
        evidence.seal_bundle(bundle['run_id'],'test')
        (self.root/'acceptance/R048.json').write_text(json.dumps({'run_id':bundle['run_id']}),encoding='utf-8')
        self.assertTrue(evidence.validate_bundle(bundle['run_id'])['valid'])
        result=factory.status('R048')
        self.assertFalse(result['execution_passed'])
        self.assertEqual(result['level'],'L1')


if __name__=='__main__': unittest.main()
