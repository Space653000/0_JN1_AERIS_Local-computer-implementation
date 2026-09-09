import hashlib
import hmac
import json
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import evidence, release_evidence as auth, taskstate, verification
from aeris_runtime.config import ROOT


class ReleaseAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        temp = ROOT / '.aeris/test-temp'
        temp.mkdir(parents=True, exist_ok=True)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(dir=temp)))
        for module, name, value in [(evidence,'EVIDENCE_ROOT',self.root/'evidence'),
                (auth,'TRUST_STORE',self.root/'trust.json'), (auth,'RECEIPTS',self.root/'receipts'),
                (taskstate,'TASK_ROOT',self.root/'tasks'), (verification,'VERIFICATION_ROOT',self.root/'verification')]:
            self.stack.enter_context(patch.object(module,name,value))
        for module in (evidence,taskstate,verification):
            self.stack.enter_context(patch.object(module,'append_event'))
        self.key = bytes(range(32))  # Deterministic test-only key; never provisioned in runtime.
        self.principal = {'key_hex':self.key.hex(), 'revoked':False,'subject_id':'reviewer-stable-id',
                          'kind':'HUMAN','allowed_gates':verification.GATES,'isolated_contexts':['isolated-review-context']}
        auth.TRUST_STORE.write_text(json.dumps({'principals':{'test-signer':self.principal}}))
        auth.RECEIPTS.mkdir()
        from aeris_runtime.blueprint_compatibility import TARGET
        now=datetime.now(timezone.utc)
        sha=evidence._git_sha()
        self.versions={
            'core_blueprint':{'repository':'Space653000/0_JN1_AERIS','commit_sha':TARGET},
            'implementation':{'repository':'Space653000/0_JN1_AERIS_Local-computer-implementation','commit_sha':sha},
            'local_checkout':{'commit_sha':sha,'dirty':False,'overlay_digest':'0'*64,'configuration_digest':'1'*64,'asset_digest':'2'*64},
            'running_service':{'implementation_sha':sha,'core_sha':TARGET,'configuration_digest':'1'*64,'asset_digest':'2'*64,
                'started_at':(now-timedelta(minutes=1)).isoformat(),'observed_at':now.isoformat()}}
        self.metadata = dict(scope='speaker-design-v1',artifact_id='design-1',
            artifact_sha256=hashlib.sha256(b'test artifact').hexdigest(),
            implementer_id='author-stable-id',implementer_context='author-context',
            version_tuple_sha256=hashlib.sha256(auth.canonical(self.versions)).hexdigest())
        self.task = taskstate.create_task('test release','author',task_id='T-auth',metadata=self.metadata)
        evidence.create_bundle('T-auth','author',run_id='RUN-auth')
        (evidence.bundle_dir('RUN-auth')/'processed/release-artifact.bin').write_bytes(b'test artifact')
        (evidence.bundle_dir('RUN-auth')/'version_tuple.json').write_text(json.dumps(self.versions))
        evidence.seal_bundle('RUN-auth','author')

    def receipt(self, gate='G4_INDEPENDENT_REVIEW', **changes):
        now = datetime.now(timezone.utc)
        payload = {**self.metadata,'task_id':'T-auth','gate':gate,'decision':'PASS',
            'signer_id':'test-signer','reviewer_context':'isolated-review-context',
            'issued_at':(now-timedelta(seconds=1)).isoformat(),
            'expires_at':(now+timedelta(hours=1)).isoformat(),
            'approval_action':'APPROVE_EXACT_ARTIFACT','run_id':'RUN-auth',
            'bundle_sha256':hashlib.sha256((evidence.bundle_dir('RUN-auth')/'bundle_manifest.json').read_bytes()).hexdigest(),**changes}
        receipt = {'payload':payload,'signature':hmac.new(self.key,auth.canonical(payload),hashlib.sha256).hexdigest()}
        (auth.RECEIPTS/(gate+'.json')).write_text(json.dumps(receipt))
        return gate

    def test_valid_receipt_resolves(self):
        self.assertEqual(auth.resolve(self.receipt(),self.task,'G4_INDEPENDENT_REVIEW')['task_id'],'T-auth')

    def test_missing_four_way_tuple_cannot_authorize_release(self):
        (evidence.bundle_dir('RUN-auth')/'version_tuple.json').unlink()
        evidence.seal_bundle('RUN-auth','author')
        with self.assertRaises(ValueError): auth.resolve(self.receipt(),self.task,'G4_INDEPENDENT_REVIEW')

    def test_signed_old_runtime_tuple_still_rejected(self):
        self.versions['running_service']['implementation_sha']='f'*40
        self.metadata['version_tuple_sha256']=hashlib.sha256(auth.canonical(self.versions)).hexdigest()
        self.task['metadata']=self.metadata
        (evidence.bundle_dir('RUN-auth')/'version_tuple.json').write_text(json.dumps(self.versions))
        evidence.seal_bundle('RUN-auth','author')
        with self.assertRaisesRegex(ValueError,'DRIFT'):
            auth.resolve(self.receipt(),self.task,'G4_INDEPENDENT_REVIEW')

    def test_claim_guard_resolves_task_bound_receipt_and_rejects_other_task(self):
        from aeris_runtime.claim_guard import validate_role_output
        ref=self.receipt()
        raw=json.dumps({'claims':[{'statement':'Bound artifact review is recorded','classification':'EVIDENCE','evidence_refs':[ref]}]})
        self.assertTrue(validate_role_output(raw,approved_evidence_refs=[ref],task_id='T-auth')['accepted'])
        self.assertFalse(validate_role_output(raw,approved_evidence_refs=[ref],task_id='T-other')['accepted'])

    def test_nonexistent_evidence_rejected(self):
        with self.assertRaises(ValueError): auth.resolve('missing',self.task,'G4_INDEPENDENT_REVIEW')

    def test_wrong_task_rejected(self):
        with self.assertRaises(ValueError): auth.resolve(self.receipt(task_id='other'),self.task,'G4_INDEPENDENT_REVIEW')

    def test_wrong_scope_rejected(self):
        with self.assertRaises(ValueError): auth.resolve(self.receipt(scope='other'),self.task,'G4_INDEPENDENT_REVIEW')

    def test_tampered_hash_rejected(self):
        ref = self.receipt()
        (evidence.bundle_dir('RUN-auth')/'processed/release-artifact.bin').write_bytes(b'tampered')
        with self.assertRaises(ValueError): auth.resolve(ref,self.task,'G4_INDEPENDENT_REVIEW')

    def test_stale_evidence_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve(self.receipt(issued_at=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()),self.task,'G4_INDEPENDENT_REVIEW')

    def test_expired_evidence_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve(self.receipt(expires_at=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()),self.task,'G4_INDEPENDENT_REVIEW')

    def test_fresh_receipt_cannot_rejuvenate_stale_source_evidence(self):
        path=evidence.bundle_dir('RUN-auth')/'run_manifest.json'
        manifest=json.loads(path.read_text())
        manifest['created_at_utc']=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()
        path.write_text(json.dumps(manifest))
        evidence.seal_bundle('RUN-auth','author')
        with self.assertRaisesRegex(ValueError,'stale'):
            auth.resolve(self.receipt(),self.task,'G4_INDEPENDENT_REVIEW')

    def test_baseline_cannot_grant_human_approval(self):
        with self.assertRaises(ValueError):
            verification.record_gate('T-auth','G5_APPROVAL','BASELINE_PASS','Human',evidence_refs=['RUN-auth'])

    def test_same_author_renamed_reviewer_rejected(self):
        self.principal['subject_id']='author-stable-id'
        auth.TRUST_STORE.write_text(json.dumps({'principals':{'test-signer':self.principal}}))
        with self.assertRaises(ValueError): auth.resolve(self.receipt(),self.task,'G4_INDEPENDENT_REVIEW')

    def test_context_collision_rejected(self):
        with self.assertRaises(ValueError): auth.resolve(self.receipt(reviewer_context='author-context'),self.task,'G4_INDEPENDENT_REVIEW')

    def test_incomplete_gates_release_rejected(self):
        path = taskstate.task_path('T-auth')
        task = self.task | {'state':'APPROVED'}
        path.write_text(json.dumps(task))
        with self.assertRaises(ValueError):
            taskstate.transition_task('T-auth','RELEASED','Human',authority='Human Chief Engineer',evidence_refs=[self.receipt('G5_APPROVAL')])

    def test_missing_human_approval_rejected(self):
        with self.assertRaises(ValueError): auth.resolve(self.receipt('G5_APPROVAL',approval_action=''),self.task,'G5_APPROVAL')

    def test_complete_gates_revalidated_at_release(self):
        for gate in verification.GATES:
            verification.record_gate('T-auth',gate,'PASS','reviewer',evidence_refs=[self.receipt(gate)],
                reviewer_role='Human Chief Engineer' if gate=='G5_APPROVAL' else 'independent_reviewer')
        self.assertTrue(verification.gate_summary('T-auth')['all_g0_g5_passed'])
        (auth.RECEIPTS/'G5_APPROVAL.json').unlink()
        self.assertFalse(verification.gate_summary('T-auth')['all_g0_g5_passed'])

    def test_full_release_requires_resolved_authority(self):
        for gate in verification.GATES:
            verification.record_gate('T-auth',gate,'PASS','reviewer',evidence_refs=[self.receipt(gate)],
                reviewer_role='Human Chief Engineer' if gate=='G5_APPROVAL' else 'independent_reviewer')
        for state in ('READY','EXECUTING','EXECUTED','EVIDENCED'):
            taskstate.transition_task('T-auth',state,'author',evidence_refs=['RUN-auth'])
        taskstate.transition_task('T-auth','VERIFIED','reviewer',authority='Independent Reviewer',
            evidence_refs=['G4_INDEPENDENT_REVIEW'])
        for state in ('APPROVED','RELEASED'):
            result = taskstate.transition_task('T-auth',state,'Human',authority='Human Chief Engineer',
                evidence_refs=['G5_APPROVAL'])
        self.assertEqual(result['state'],'RELEASED')
