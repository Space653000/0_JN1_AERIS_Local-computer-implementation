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
        for module, name, value in [
            (evidence, 'EVIDENCE_ROOT', self.root / 'evidence'),
            (auth, 'TRUST_STORE', self.root / 'trust.json'),
            (auth, 'RECEIPTS', self.root / 'receipts'),
            (taskstate, 'TASK_ROOT', self.root / 'tasks'),
            (verification, 'VERIFICATION_ROOT', self.root / 'verification'),
        ]:
            self.stack.enter_context(patch.object(module, name, value))
        for module in (evidence, taskstate, verification):
            self.stack.enter_context(patch.object(module, 'append_event'))

        self.reviewer_key = bytes(range(32))
        self.implementer_key = bytes(range(32, 64))
        self.reviewer = {
            'key_hex': self.reviewer_key.hex(),
            'revoked': False,
            'subject_id': 'reviewer-stable-id',
            'kind': 'HUMAN',
            'human_authority': 'Human Chief Engineer',
            'allowed_gates': verification.GATES,
            'isolated_contexts': ['isolated-review-context'],
        }
        self.implementer = {
            'key_hex': self.implementer_key.hex(),
            'revoked': False,
            'subject_id': 'author-stable-id',
            'kind': 'IMPLEMENTER',
            'can_implement': True,
            'execution_contexts': ['author-context'],
        }
        self.trust = {
            'principals': {
                'test-reviewer': self.reviewer,
                'test-implementer': self.implementer,
            }
        }
        auth.TRUST_STORE.write_text(json.dumps(self.trust))
        auth.RECEIPTS.mkdir()

        from aeris_runtime.blueprint_compatibility import TARGET
        now = datetime.now(timezone.utc)
        sha = evidence._git_sha()
        self.versions = {
            'core_blueprint': {
                'repository': 'Space653000/0_JN1_AERIS',
                'commit_sha': TARGET,
            },
            'implementation': {
                'repository': 'Space653000/0_JN1_AERIS_Local-computer-implementation',
                'commit_sha': sha,
            },
            'local_checkout': {
                'commit_sha': sha,
                'dirty': False,
                'overlay_digest': '0' * 64,
                'configuration_digest': '1' * 64,
                'asset_digest': '2' * 64,
            },
            'running_service': {
                'implementation_sha': sha,
                'core_sha': TARGET,
                'configuration_digest': '1' * 64,
                'asset_digest': '2' * 64,
                'started_at': (now - timedelta(minutes=1)).isoformat(),
                'observed_at': now.isoformat(),
            },
        }
        self.metadata = {
            'scope': 'speaker-design-v1',
            'artifact_id': 'design-1',
            'artifact_sha256': hashlib.sha256(b'test artifact').hexdigest(),
            'implementer_id': 'author-stable-id',
            'implementer_context': 'author-context',
            'version_tuple_sha256': hashlib.sha256(auth.canonical(self.versions)).hexdigest(),
            'implementer_attestation_ref': 'IMPLEMENTER_ATTESTATION',
        }
        self.task = taskstate.create_task(
            'test release',
            'author-stable-id',
            task_id='T-auth',
            metadata=self.metadata,
        )
        evidence.create_bundle('T-auth', 'author-stable-id', run_id='RUN-auth')
        (evidence.bundle_dir('RUN-auth') / 'processed/release-artifact.bin').write_bytes(b'test artifact')
        (evidence.bundle_dir('RUN-auth') / 'version_tuple.json').write_text(json.dumps(self.versions))
        evidence.seal_bundle('RUN-auth', 'author-stable-id')

    def _sign(self, payload, key):
        return {
            'payload': payload,
            'signature': hmac.new(key, auth.canonical(payload), hashlib.sha256).hexdigest(),
        }

    def implementer_attestation(self, **changes):
        now = datetime.now(timezone.utc)
        bundle_hash = hashlib.sha256(
            (evidence.bundle_dir('RUN-auth') / 'bundle_manifest.json').read_bytes()
        ).hexdigest()
        payload = {
            'type': auth.IMPLEMENTER_PURPOSE,
            'signer_id': 'test-implementer',
            'task_id': self.task['task_id'],
            'scope': self.metadata['scope'],
            'artifact_id': self.metadata['artifact_id'],
            'artifact_sha256': self.metadata['artifact_sha256'],
            'implementer_id': self.metadata['implementer_id'],
            'implementer_context': self.metadata['implementer_context'],
            'version_tuple_sha256': self.metadata['version_tuple_sha256'],
            'run_id': 'RUN-auth',
            'bundle_sha256': bundle_hash,
            'issued_at': (now - timedelta(seconds=1)).isoformat(),
            'expires_at': (now + timedelta(hours=1)).isoformat(),
            **changes,
        }
        receipt = self._sign(payload, self.implementer_key)
        (auth.RECEIPTS / 'IMPLEMENTER_ATTESTATION.json').write_text(json.dumps(receipt))
        return 'IMPLEMENTER_ATTESTATION'

    def receipt(self, gate='G4_INDEPENDENT_REVIEW', *, signer_id='test-reviewer',
                signing_key=None, refresh_implementer=True, **changes):
        if refresh_implementer:
            self.implementer_attestation()
        now = datetime.now(timezone.utc)
        payload = {
            **self.metadata,
            'task_id': 'T-auth',
            'gate': gate,
            'decision': 'PASS',
            'signer_id': signer_id,
            'reviewer_context': 'isolated-review-context',
            'issued_at': (now - timedelta(seconds=1)).isoformat(),
            'expires_at': (now + timedelta(hours=1)).isoformat(),
            'approval_action': 'APPROVE_EXACT_ARTIFACT',
            'run_id': 'RUN-auth',
            'bundle_sha256': hashlib.sha256(
                (evidence.bundle_dir('RUN-auth') / 'bundle_manifest.json').read_bytes()
            ).hexdigest(),
            **changes,
        }
        receipt = self._sign(payload, signing_key or self.reviewer_key)
        (auth.RECEIPTS / (gate + '.json')).write_text(json.dumps(receipt))
        return gate

    def test_valid_receipt_resolves_two_authoritative_subjects(self):
        resolved = auth.resolve(self.receipt(), self.task, 'G4_INDEPENDENT_REVIEW')
        authority = resolved['_resolved_authority']
        self.assertEqual(authority['implementer_subject_id'], 'author-stable-id')
        self.assertEqual(authority['reviewer_subject_id'], 'reviewer-stable-id')

    def test_nonexistent_evidence_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve('missing', self.task, 'G4_INDEPENDENT_REVIEW')

    def test_wrong_task_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve(self.receipt(task_id='other'), self.task, 'G4_INDEPENDENT_REVIEW')

    def test_wrong_scope_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve(self.receipt(scope='other'), self.task, 'G4_INDEPENDENT_REVIEW')

    def test_wrong_artifact_binding_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve(self.receipt(artifact_id='other-artifact'), self.task, 'G4_INDEPENDENT_REVIEW')

    def test_tampered_hash_rejected(self):
        ref = self.receipt()
        (evidence.bundle_dir('RUN-auth') / 'processed/release-artifact.bin').write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            auth.resolve(ref, self.task, 'G4_INDEPENDENT_REVIEW')

    def test_stale_evidence_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve(
                self.receipt(issued_at=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat()),
                self.task,
                'G4_INDEPENDENT_REVIEW',
            )

    def test_expired_evidence_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve(
                self.receipt(expires_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()),
                self.task,
                'G4_INDEPENDENT_REVIEW',
            )

    def test_fresh_receipt_cannot_rejuvenate_stale_source_evidence(self):
        path = evidence.bundle_dir('RUN-auth') / 'run_manifest.json'
        manifest = json.loads(path.read_text())
        manifest['created_at_utc'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        path.write_text(json.dumps(manifest))
        evidence.seal_bundle('RUN-auth', 'author-stable-id')
        with self.assertRaisesRegex(ValueError, 'stale'):
            auth.resolve(self.receipt(), self.task, 'G4_INDEPENDENT_REVIEW')

    def test_missing_implementer_attestation_rejected(self):
        ref = self.receipt()
        (auth.RECEIPTS / 'IMPLEMENTER_ATTESTATION.json').unlink()
        with self.assertRaises(ValueError):
            auth.resolve(ref, self.task, 'G4_INDEPENDENT_REVIEW')

    def test_tampered_implementer_attestation_rejected(self):
        ref = self.receipt()
        path = auth.RECEIPTS / 'IMPLEMENTER_ATTESTATION.json'
        receipt = json.loads(path.read_text())
        receipt['payload']['implementer_context'] = 'forged-context'
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'tampered'):
            auth.resolve(ref, self.task, 'G4_INDEPENDENT_REVIEW')

    def test_stale_implementer_attestation_rejected(self):
        self.implementer_attestation(
            issued_at=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        )
        with self.assertRaisesRegex(ValueError, 'implementer attestation'):
            auth.resolve(
                self.receipt(refresh_implementer=False),
                self.task,
                'G4_INDEPENDENT_REVIEW',
            )

    def test_caller_cannot_relabel_implementer_to_bypass_independence(self):
        self.metadata['implementer_id'] = 'innocent-third-party'
        self.task['metadata'] = dict(self.metadata)
        taskstate.task_path('T-auth').write_text(json.dumps(self.task))
        with self.assertRaisesRegex(ValueError, 'alias'):
            auth.resolve(self.receipt(), self.task, 'G4_INDEPENDENT_REVIEW')

    def test_reviewer_alias_collision_rejected_even_with_different_signer_id(self):
        alias_key = bytes(range(64, 96))
        self.trust['principals']['reviewer-alias'] = {
            'key_hex': alias_key.hex(),
            'revoked': False,
            'subject_id': 'author-stable-id',
            'kind': 'HUMAN',
            'human_authority': 'Human Chief Engineer',
            'allowed_gates': verification.GATES,
            'isolated_contexts': ['isolated-review-context'],
        }
        auth.TRUST_STORE.write_text(json.dumps(self.trust))
        with self.assertRaisesRegex(ValueError, 'collision'):
            auth.resolve(
                self.receipt(signer_id='reviewer-alias', signing_key=alias_key),
                self.task,
                'G4_INDEPENDENT_REVIEW',
            )

    def test_same_credential_relabelled_as_different_subject_is_rejected(self):
        self.trust['principals']['credential-alias'] = {
            'key_hex': self.implementer_key.hex(),
            'revoked': False,
            'subject_id': 'different-label-same-credential',
            'kind': 'HUMAN',
            'human_authority': 'Human Chief Engineer',
            'allowed_gates': verification.GATES,
            'isolated_contexts': ['isolated-review-context'],
        }
        auth.TRUST_STORE.write_text(json.dumps(self.trust))
        with self.assertRaisesRegex(ValueError, 'credential alias collision'):
            auth.resolve(
                self.receipt(
                    signer_id='credential-alias',
                    signing_key=self.implementer_key,
                ),
                self.task,
                'G4_INDEPENDENT_REVIEW',
            )

    def test_context_collision_rejected(self):
        self.reviewer['isolated_contexts'].append('author-context')
        auth.TRUST_STORE.write_text(json.dumps(self.trust))
        with self.assertRaisesRegex(ValueError, 'context collision'):
            auth.resolve(
                self.receipt(reviewer_context='author-context'),
                self.task,
                'G4_INDEPENDENT_REVIEW',
            )

    def test_missing_four_way_tuple_cannot_authorize_release(self):
        (evidence.bundle_dir('RUN-auth') / 'version_tuple.json').unlink()
        evidence.seal_bundle('RUN-auth', 'author-stable-id')
        with self.assertRaises(ValueError):
            auth.resolve(self.receipt(), self.task, 'G4_INDEPENDENT_REVIEW')

    def test_dirty_checkout_cannot_authorize_release(self):
        self.versions['local_checkout']['dirty'] = True
        self.metadata['version_tuple_sha256'] = hashlib.sha256(auth.canonical(self.versions)).hexdigest()
        self.task['metadata'] = dict(self.metadata)
        taskstate.task_path('T-auth').write_text(json.dumps(self.task))
        (evidence.bundle_dir('RUN-auth') / 'version_tuple.json').write_text(json.dumps(self.versions))
        evidence.seal_bundle('RUN-auth', 'author-stable-id')
        with self.assertRaisesRegex(ValueError, 'clean observed'):
            auth.resolve(self.receipt(), self.task, 'G4_INDEPENDENT_REVIEW')

    def test_signed_old_runtime_tuple_still_rejected(self):
        self.versions['running_service']['implementation_sha'] = 'f' * 40
        self.metadata['version_tuple_sha256'] = hashlib.sha256(auth.canonical(self.versions)).hexdigest()
        self.task['metadata'] = dict(self.metadata)
        taskstate.task_path('T-auth').write_text(json.dumps(self.task))
        (evidence.bundle_dir('RUN-auth') / 'version_tuple.json').write_text(json.dumps(self.versions))
        evidence.seal_bundle('RUN-auth', 'author-stable-id')
        with self.assertRaisesRegex(ValueError, 'DRIFT'):
            auth.resolve(self.receipt(), self.task, 'G4_INDEPENDENT_REVIEW')

    def test_claim_guard_resolves_task_bound_receipt_and_rejects_other_task(self):
        from aeris_runtime.claim_guard import validate_role_output
        ref = self.receipt()
        raw = json.dumps({
            'claims': [{
                'statement': 'Bound artifact review is recorded',
                'classification': 'EVIDENCE',
                'evidence_refs': [ref],
            }]
        })
        self.assertTrue(
            validate_role_output(raw, approved_evidence_refs=[ref], task_id='T-auth')['accepted']
        )
        self.assertFalse(
            validate_role_output(raw, approved_evidence_refs=[ref], task_id='T-other')['accepted']
        )

    def test_baseline_cannot_grant_human_approval(self):
        with self.assertRaises(ValueError):
            verification.record_gate(
                'T-auth', 'G5_APPROVAL', 'BASELINE_PASS',
                'Human', evidence_refs=['RUN-auth']
            )

    def test_incomplete_gates_release_rejected(self):
        path = taskstate.task_path('T-auth')
        task = self.task | {'state': 'APPROVED'}
        path.write_text(json.dumps(task))
        with self.assertRaises(ValueError):
            taskstate.transition_task(
                'T-auth',
                'RELEASED',
                'reviewer-stable-id',
                authority='Human Chief Engineer',
                evidence_refs=[self.receipt('G5_APPROVAL')],
            )

    def test_missing_human_approval_rejected(self):
        with self.assertRaises(ValueError):
            auth.resolve(
                self.receipt('G5_APPROVAL', approval_action=''),
                self.task,
                'G5_APPROVAL',
            )

    def test_non_chief_human_cannot_grant_g5(self):
        self.reviewer['human_authority'] = 'Human Observer'
        auth.TRUST_STORE.write_text(json.dumps(self.trust))
        with self.assertRaisesRegex(ValueError, 'Human approval'):
            auth.resolve(self.receipt('G5_APPROVAL'), self.task, 'G5_APPROVAL')

    def test_complete_gates_revalidated_at_release(self):
        for gate in verification.GATES:
            verification.record_gate(
                'T-auth',
                gate,
                'PASS',
                'reviewer-stable-id',
                evidence_refs=[self.receipt(gate)],
                reviewer_role='Human Chief Engineer' if gate == 'G5_APPROVAL' else 'independent_reviewer',
            )
        self.assertTrue(verification.gate_summary('T-auth')['all_g0_g5_passed'])
        (auth.RECEIPTS / 'G5_APPROVAL.json').unlink()
        self.assertFalse(verification.gate_summary('T-auth')['all_g0_g5_passed'])

    def test_verification_record_contains_authenticated_reviewer_subject(self):
        state = verification.record_gate(
            'T-auth',
            'G4_INDEPENDENT_REVIEW',
            'PASS',
            'display-name-only',
            evidence_refs=[self.receipt()],
            reviewer_role='independent_reviewer',
        )
        self.assertEqual(
            state['gates']['G4_INDEPENDENT_REVIEW']['reviewer_subject_ids'],
            ['reviewer-stable-id'],
        )

    def test_full_release_requires_resolved_authority(self):
        for gate in verification.GATES:
            verification.record_gate(
                'T-auth',
                gate,
                'PASS',
                'reviewer-stable-id',
                evidence_refs=[self.receipt(gate)],
                reviewer_role='Human Chief Engineer' if gate == 'G5_APPROVAL' else 'independent_reviewer',
            )
        for state in ('READY', 'EXECUTING', 'EXECUTED', 'EVIDENCED'):
            taskstate.transition_task('T-auth', state, 'author-stable-id', evidence_refs=['RUN-auth'])
        taskstate.transition_task(
            'T-auth',
            'VERIFIED',
            'reviewer-stable-id',
            authority='Independent Reviewer',
            evidence_refs=['G4_INDEPENDENT_REVIEW'],
        )
        taskstate.transition_task(
            'T-auth',
            'APPROVED',
            'reviewer-stable-id',
            authority='Human Chief Engineer',
            evidence_refs=['G5_APPROVAL'],
        )
        result = taskstate.transition_task(
            'T-auth',
            'RELEASED',
            'reviewer-stable-id',
            authority='Human Chief Engineer',
            evidence_refs=['G5_APPROVAL'],
        )
        self.assertEqual(result['state'], 'RELEASED')


if __name__ == '__main__':
    unittest.main()
