import tempfile
import json
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import audit,controlplane,evidence,reproduction,taskstate,verification,workflow
from aeris_runtime.config import ROOT
from aeris_runtime.engineering import factory,harness,role_acceptance,domain_review
from aeris_runtime.engineering.orchestration import run_role
from tests.test_speaker_power_domain import BASE
from tests.test_tws_domain_method import BASE as TWS_BASE
from tests.test_microphone_measurement_domain import BASE as MIC_BASE,SKILL as MIC_SKILL


class RoleWorkflowExecutionTests(unittest.TestCase):
    def test_evidenced_power_workflow_does_not_invent_a_qualified_reviewer(self):
        base=ROOT/'.aeris/test-temp'; base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as directory,ExitStack() as stack:
            root=Path(directory)
            for module,name,value in (
                (controlplane,'DB_PATH',root/'control.sqlite3'),(factory,'STATE',root/'factory'),
                (role_acceptance,'STATE',root/'role-acceptance'),(harness,'DB',root/'memory.sqlite3'),
                (taskstate,'TASK_ROOT',root/'tasks'),(evidence,'EVIDENCE_ROOT',root/'evidence'),
                (verification,'VERIFICATION_ROOT',root/'verification'),(workflow,'WORKFLOW_ROOT',root/'workflows'),
                (reproduction,'REPRO_ROOT',root/'reproduction'),(audit,'AUDIT_DIR',root/'audit'),
                (audit,'AUDIT_FILE',root/'audit/audit.jsonl'),(audit,'LEDGER_PATH',root/'audit/audit.jsonl'),
                (audit,'LOCK_FILE',root/'audit/.lock')):
                stack.enter_context(patch.object(module,name,value))
            self.assertTrue(role_acceptance.RoleAcceptanceFactory().evaluate('R016')['execution_passed'])
            result=run_role('R016','speaker-power-distortion-baseline',
                            {**BASE,'harmonic_rms_pa':[0.1,0.0]},objective='Synthetic power distortion investigation',source_kind='SYNTHETIC')
            self.assertEqual(result['state'],'EVIDENCED')
            sealed=json.loads((evidence.bundle_dir(result['evidence_run_id'])/'raw/engineering-context.json').read_text())
            self.assertEqual(sealed['applicability']['transducer'],'Speaker')
            self.assertEqual(sealed['applicability']['lifecycle'],'EVT')
            self.assertEqual(sealed['applicability']['risk'],'R1')
            self.assertEqual(sealed['skill_id'],'speaker-power-distortion-baseline')
            self.assertEqual(sealed['required_review_domains'],['speaker-nonlinear','speaker-thermal'])
            self.assertEqual(result['review']['decision'],'REVIEW_BLOCKED')
            self.assertIsNone(result['pod']['reviewer'])
            self.assertEqual(result['pod']['executors'],['R016'])
            self.assertFalse(result['human_approval'])
            self.assertEqual(result['numerical_result']['values']['disposition'],'DESIGN_REVISION_REQUIRED')
            self.assertEqual(controlplane.ControlStore().list_tasks()[0]['state'],'EVIDENCED')
            self.assertEqual(reproduction.reproduce_run(result['evidence_run_id'])['result'],'PASS')
            self.assertTrue(harness.Harness().verify()['valid'])
            # A role-level L2 result cannot silently authorize all shared Skills.
            shared=factory.catalog.definitions()['harmonic-noise-analysis']['fixture']['input']
            with self.assertRaisesRegex(ValueError,'execution evidence for this Skill'):
                run_role('R016','harmonic-noise-analysis',shared,objective='Unproven shared Skill')
            for override in ({'reviewer':'R098'},{'execution_role_id':'R075'}):
                with self.assertRaisesRegex(ValueError,'context override'):
                    run_role('R016','speaker-power-distortion-baseline',BASE,objective='Illegal override',context=override)
            self.assertEqual(len(controlplane.ControlStore().list_tasks()),1)
            for role in ('R010','R075'):
                self.assertTrue(role_acceptance.RoleAcceptanceFactory().evaluate(role)['execution_passed'])
            rejected=run_role('R016','speaker-power-distortion-baseline',
                             {**BASE,'harmonic_rms_pa':[0.1,0.0]},objective='Review excessive distortion',source_kind='SYNTHETIC')
            self.assertEqual(rejected['review']['decision'],'DESIGN_REVISION_REQUIRED')
            self.assertEqual(len(rejected['review']['reviews']),2)
            corrected=run_role('R016','speaker-power-distortion-baseline',BASE,objective='Review reduced distortion',source_kind='SYNTHETIC')
            self.assertEqual(corrected['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertTrue(corrected['pod']['pod_complete'])
            self.assertEqual({r['role_id'] for r in corrected['pod']['reviewers']},{'R010','R075'})
            review_id=corrected['review']['review_run_id']
            self.assertTrue(domain_review.review_status(review_id)['valid'])
            mutable=workflow.load_workflow(corrected['workflow_id'])
            mutable['engineering_context']['applicability']['risk']='R4'
            workflow._write(mutable)
            self.assertTrue(domain_review.review_status(review_id)['valid'])
            self.assertEqual(reproduction.reproduce_run(corrected['evidence_run_id'])['result'],'PASS')
            self.assertTrue(harness.Harness().verify()['valid'])
            # Sealed review tampering and missing qualification fail closed.
            (evidence.bundle_dir(review_id)/'processed/domain-review.json').write_text('{}',encoding='utf-8')
            self.assertFalse(domain_review.review_status(review_id)['valid'])
            qualifications=(('R048','tws-fit-anc-call-baseline'),('R005','tws-anc-domain-review'),
                            ('R029','tws-fit-capture-domain-review'))
            for role,skill in qualifications:
                self.assertTrue(role_acceptance.RoleAcceptanceFactory().evaluate(role,skill)['execution_passed'])
            tws=run_role('R048','tws-fit-anc-call-baseline',TWS_BASE,objective='Review TWS fit and ANC',source_kind='SYNTHETIC')
            self.assertEqual(tws['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual({r['role_id'] for r in tws['pod']['reviewers']},{'R005','R029'})
            self.assertTrue(domain_review.review_status(tws['review']['review_run_id'])['valid'])
            # A self-consistent forged excursion verdict must not evade review.
            result_path=evidence.bundle_dir(tws['evidence_run_id'])/'processed/skill_result.json'
            input_path=evidence.bundle_dir(tws['evidence_run_id'])/'raw/engineering-input.json'
            saved_output=json.loads(result_path.read_text())
            # Counter-hypotheses and check/action contracts are review assertions.
            for mutation in ('counter','missing','wrong_action','fake_professional'):
                candidate=json.loads(json.dumps(saved_output))
                if mutation=='counter': candidate['values']['counter_hypotheses']=['Full loop stability is proven and seal leakage is impossible']
                elif mutation=='missing': candidate['values']['checks'].pop()
                elif mutation=='wrong_action': candidate['values']['checks'][0]['on_failure']='IGNORE_THE_LEAK'
                else: candidate['professional_tool_verified']=True
                result_path.write_text(json.dumps(candidate),encoding='utf-8')
                evidence.seal_bundle(tws['evidence_run_id'],'test fixture reseal')
                with self.subTest(mutation=mutation):
                    self.assertNotEqual(domain_review.review_bundle(tws['evidence_run_id'])['decision'],'BOUNDED_REVIEW_ACCEPT')
            result_path.write_text(json.dumps(saved_output),encoding='utf-8')
            altered_inputs=json.loads(input_path.read_text()); altered_inputs['driver_peak_excursion_mm']=1.0
            altered_output=json.loads(result_path.read_text()); altered_output['input_sha256']=factory.catalog.digest(altered_inputs)
            input_path.write_text(json.dumps(altered_inputs),encoding='utf-8')
            result_path.write_text(json.dumps(altered_output),encoding='utf-8')
            evidence.seal_bundle(tws['evidence_run_id'],'test fixture reseal')
            self.assertNotEqual(domain_review.review_bundle(tws['evidence_run_id'])['decision'],'BOUNDED_REVIEW_ACCEPT')
            # A missing sealed context cannot borrow the mutable workflow context.
            (evidence.bundle_dir(tws['evidence_run_id'])/'raw/engineering-context.json').write_text('{}',encoding='utf-8')
            evidence.seal_bundle(tws['evidence_run_id'],'test fixture reseal')
            self.assertEqual(domain_review.review_bundle(tws['evidence_run_id'])['decision'],'REVIEW_BLOCKED')
            self.assertTrue(role_acceptance.RoleAcceptanceFactory().evaluate('R033')['execution_passed'])
            mic=run_role('R033',MIC_SKILL,MIC_BASE,objective='Supplied microphone reference investigation',source_kind='SYNTHETIC')
            self.assertEqual(mic['state'],'EVIDENCED')
            self.assertEqual(mic['review']['decision'],'REVIEW_BLOCKED')
            self.assertEqual(reproduction.reproduce_run(mic['evidence_run_id'])['result'],'PASS')
            self.assertFalse(mic['numerical_result']['values']['capsule_overload_verified'])
            for role in ('R028','R030'):
                self.assertTrue(role_acceptance.RoleAcceptanceFactory().evaluate(role)['execution_passed'])
            reviewed_mic=run_role('R033',MIC_SKILL,MIC_BASE,objective='Independently review microphone reference',source_kind='SYNTHETIC')
            self.assertEqual(reviewed_mic['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual({r['role_id'] for r in reviewed_mic['pod']['reviewers']},{'R028','R030'})
            self.assertTrue(domain_review.review_status(reviewed_mic['review']['review_run_id'])['valid'])
            unresolved_mic=run_role('R033',MIC_SKILL,{**MIC_BASE,'frontend_noise_rms_v':0.00001},objective='Challenge unresolved microphone floor',source_kind='SYNTHETIC')
            self.assertEqual(unresolved_mic['review']['decision'],'DESIGN_REVISION_REQUIRED')


if __name__=='__main__': unittest.main()
