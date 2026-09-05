"""Role-domain execution has its own questions, oracles and sealed evidence."""
import json
import copy
import sqlite3
import tempfile
import unittest
from contextlib import closing
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import audit, evidence
from aeris_runtime.config import ROOT


class RoleAcceptanceTests(unittest.TestCase):
    def test_compact_role_fixture_mutations_are_bounded_existing_and_non_aliasing(self):
        from aeris_runtime.engineering.role_acceptance import apply_case_mutations
        target={'parameters':{'channels':[{'counter':1}]}}
        patch_value={'counter':7}
        apply_case_mutations(target,[{'path':'parameters.channels.0','value':patch_value}])
        patch_value['counter']=9
        self.assertEqual(target['parameters']['channels'][0]['counter'],7)
        for mutations in ([{'path':'parameters.channels.1','value':{}}],
                          [{'path':'parameters.missing','value':0}],
                          [{'path':'parameters..channels','value':0}],
                          [{'path':'parameters.channels','value':[]},{'path':'parameters.channels','value':[]}],
                          [{'path':'parameters','value':0}]*41):
            with self.subTest(mutations=mutations),self.assertRaises((ValueError,KeyError)):
                apply_case_mutations({'parameters':{'channels':[{}]}},mutations)

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
        index=self.root/'acceptance/R048/tws-fit-anc-call-baseline.json'
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
        self.assertEqual(result['case_count'],13)
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
        index=self.root/'acceptance/R016/speaker-power-distortion-baseline.json'
        index.write_text(json.dumps({'role_id':'R016','skill_id':'speaker-power-distortion-baseline','run_id':tws['run_id']}),encoding='utf-8')
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
            self.assertEqual(matrix['total_role_golden_cases'],311)
            self.assertEqual(matrix['total_role_golden_suites'],25)
            fixture=api.get('/api/v1/capabilities/fixture/R048?skill=tws-fit-anc-call-baseline')
            self.assertEqual(fixture['source_kind'],'SYNTHETIC')
            self.assertEqual(fixture['fixture']['input']['feedback_delay_ms'],0.5)
            self.assertIn('tws-fit-anc-call-baseline',[s['skill_id'] for s in api.get('/api/v1/capabilities/skills')['skills']])

    def test_multi_capability_receipts_are_independent_and_aggregate_is_fail_closed(self):
        from aeris_runtime.engineering import factory as capability_factory, role_acceptance
        pack=capability_factory.load_pack('R010')
        first=copy.deepcopy(pack['domain_execution_contracts'][0])
        second_source=capability_factory.load_pack('R075')['domain_execution_contracts'][0]
        second={**copy.deepcopy(second_source),'suite':'golden/roles/R010/thermal.json'}
        current=copy.deepcopy(pack)
        current['domain_execution_contracts']=[first]
        suites={first['skill_id']:json.loads((ROOT/first['suite']).read_text()),
                second['skill_id']:json.loads((ROOT/second_source['suite']).read_text())}
        suites[second['skill_id']]['role_id']='R010'

        def load_contract(role_id,skill_id=None):
            self.assertEqual(role_id,'R010')
            contracts=current['domain_execution_contracts']
            if skill_id is None:
                if len(contracts)!=1: raise ValueError('explicit Skill ID required')
                skill_id=contracts[0]['skill_id']
            contract=next(c for c in contracts if c['skill_id']==skill_id)
            return current,copy.deepcopy(suites[contract['skill_id']])

        runner=role_acceptance.RoleAcceptanceFactory(self.root/'acceptance')
        with patch.object(capability_factory,'load_pack',return_value=current), \
             patch.object(capability_factory,'contract_errors',return_value=[]), \
             patch.object(role_acceptance,'load_contract',side_effect=load_contract), \
             patch.object(role_acceptance,'capability_artifact_digest',side_effect=lambda p,c,s: capability_factory.catalog.digest({'contract':c,'suite':s})):
            passed_a=runner.evaluate('R010',first['skill_id'])
            self.assertTrue(passed_a['execution_passed'])
            current['domain_execution_contracts'].append(second)
            still_a=runner.status_for_skill('R010',first['skill_id'])
            self.assertTrue(still_a['execution_passed'])
            partial=runner.status('R010')
            self.assertEqual(partial['level'],'L1')
            self.assertEqual(partial['passed_skill_ids'],[first['skill_id']])
            self.assertEqual(partial['missing_skill_ids'],[second['skill_id']])
            self.assertTrue(runner.evaluate('R010',second['skill_id'])['execution_passed'])
            complete=runner.status('R010')
            self.assertEqual(complete['level'],'L2')
            self.assertEqual(complete['missing_skill_ids'],[])
            self.assertEqual(complete['declared_capability_count'],2)
            current['domain_execution_contracts']=[first]
            removed=runner.status('R010')
            self.assertEqual(removed['level'],'L2')
            self.assertTrue(runner.status_for_skill('R010',first['skill_id'])['execution_passed'])
            self.assertEqual(len(removed['composition_history']),3)
            self.assertEqual(removed['composition_history'][0]['contract_set_sha256'],
                             removed['composition_history'][-1]['contract_set_sha256'])
            with closing(sqlite3.connect(runner._composition_db())) as connection:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute('DELETE FROM composition WHERE role_id=? AND sequence>1',('R010',))
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute('UPDATE composition SET record_json=? WHERE role_id=? AND sequence=2',('{}','R010'))
            self.assertEqual(len(runner.composition_history('R010')),3)
            current['domain_execution_contracts']=[first,second]
            current['domain_execution_contracts'][0]={**first,'scope':first['scope']+' changed'}
            self.assertFalse(runner.status_for_skill('R010',first['skill_id'])['execution_passed'])
            self.assertTrue(runner.status_for_skill('R010',second['skill_id'])['execution_passed'])
            with closing(sqlite3.connect(runner._composition_db())) as connection:
                connection.execute('DROP TRIGGER composition_no_delete')
                connection.execute('DROP TRIGGER composition_no_update')
                connection.execute('DELETE FROM composition WHERE role_id=? AND sequence>1',('R010',))
                connection.commit()
            with self.assertRaisesRegex(ValueError,'anchor'):
                runner.composition_history('R010')

    def test_deleted_composition_authorities_cannot_reset_existing_receipt_history(self):
        from aeris_runtime.engineering import role_acceptance
        runner=role_acceptance.RoleAcceptanceFactory(self.root/'acceptance')
        self.assertTrue(runner.evaluate('R010')['execution_passed'])
        db=runner._composition_db(); anchors=runner._composition_anchor_dir('R010')
        db.unlink()
        for path in anchors.glob('*.json'): path.unlink()
        status=runner.status('R010')
        self.assertEqual(status['level'],'L1')
        self.assertFalse(status['execution_passed'])
        self.assertFalse(status['composition_history_valid'])
        self.assertIn('ledger missing',status['reason'])

    def test_legacy_locator_and_ambiguous_contract_request_cannot_qualify(self):
        from aeris_runtime.engineering import factory as capability_factory,role_acceptance
        runner=role_acceptance.RoleAcceptanceFactory(self.root/'acceptance')
        valid=runner.evaluate('R010')
        legacy=self.root/'acceptance/R075.json'
        legacy.write_text(json.dumps({'role_id':'R075','run_id':valid['run_id']}),encoding='utf-8')
        self.assertFalse(runner.status_for_skill('R075','speaker-thermal-domain-review')['execution_passed'])
        pack=copy.deepcopy(capability_factory.load_pack('R010'))
        pack['domain_execution_contracts'].append({**copy.deepcopy(pack['domain_execution_contracts'][0]),
                                                   'skill_id':'speaker-thermal-domain-review',
                                                   'suite':'golden/roles/R010/thermal.json'})
        with patch.object(capability_factory,'load_pack',return_value=pack), \
             patch.object(capability_factory,'contract_errors',return_value=[]):
            with self.assertRaisesRegex(ValueError,'explicit Skill ID'):
                role_acceptance.load_contract('R010')

    def test_capability_source_fingerprint_ignores_unrelated_handler_registration(self):
        from aeris_runtime.engineering import domain_methods,domain_review,microphone_domain,role_acceptance
        pack,suite=role_acceptance.load_contract('R010','speaker-nonlinear-domain-review')
        contract=pack['domain_execution_contracts'][0]
        baseline=role_acceptance.capability_artifact_digest(pack,contract,suite)
        unrelated=domain_methods._review_handler('unrelated-future-domain')
        with patch.dict(domain_methods.HANDLERS,{'unrelated-future-domain-review':unrelated}):
            self.assertEqual(role_acceptance.capability_artifact_digest(pack,contract,suite),baseline)

        def changed_handler(params):
            return {'changed':bool(params)}
        with patch.dict(domain_methods.HANDLERS,{contract['skill_id']:changed_handler}):
            self.assertNotEqual(role_acceptance.capability_artifact_digest(pack,contract,suite),baseline)

        original_review=domain_review.capability_source_digest('speaker-nonlinear')
        def stricter_assertion(actual,wanted):
            return actual==wanted
        with patch.object(domain_review,'_same_assertion',stricter_assertion):
            self.assertNotEqual(domain_review.capability_source_digest('speaker-nonlinear'),original_review)

        mic_pack,mic_suite=role_acceptance.load_contract('R033','microphone-reference-noise-headroom-baseline')
        mic_contract=mic_pack['domain_execution_contracts'][0]
        mic_baseline=role_acceptance.capability_artifact_digest(mic_pack,mic_contract,mic_suite)
        def relaxed_db_limit(actual,limit):
            return actual<=limit+100
        with patch.object(microphone_domain,'db_at_most',relaxed_db_limit):
            self.assertNotEqual(role_acceptance.capability_artifact_digest(mic_pack,mic_contract,mic_suite),mic_baseline)

    def assert_resealed_rejected(self,factory,record):
        bundle=evidence.create_bundle('SYNTHETIC-MUTATION','test')
        path=evidence.bundle_dir(bundle['run_id'])/'processed/role-domain-execution.json'
        path.write_text(json.dumps(record),encoding='utf-8')
        evidence.seal_bundle(bundle['run_id'],'test')
        index=self.root/'acceptance/R048/tws-fit-anc-call-baseline.json'
        index.parent.mkdir(parents=True,exist_ok=True)
        index.write_text(json.dumps({'role_id':'R048','skill_id':'tws-fit-anc-call-baseline','run_id':bundle['run_id']}),encoding='utf-8')
        self.assertTrue(evidence.validate_bundle(bundle['run_id'])['valid'])
        result=factory.status('R048')
        self.assertFalse(result['execution_passed'])
        self.assertEqual(result['level'],'L1')


if __name__=='__main__': unittest.main()
