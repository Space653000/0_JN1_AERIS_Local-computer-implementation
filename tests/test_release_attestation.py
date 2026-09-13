"""P6.5: the production release-attestation tooling actually interoperates
with release_evidence.py's existing signature-verification engine end to
end -- prepare_release_task() must produce a task/Evidence bundle/
implementer receipt that a genuine Human G5 receipt (signed with a key this
test controls, standing in for the Human's own) resolves successfully, and
current_release_authority_status() must report the honest state at every
step (never aligned before a real receipt exists)."""
import hashlib
import hmac
import json
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import (
    audit,
    evidence,
    release_attestation as ra,
    release_evidence as auth,
    taskstate,
)
from aeris_runtime.config import ROOT


class ReleaseAttestationTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        temp = ROOT / ".aeris/test-temp"
        temp.mkdir(parents=True, exist_ok=True)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(dir=temp)))
        for module, name, value in [
            (evidence, "EVIDENCE_ROOT", self.root / "evidence"),
            (auth, "TRUST_STORE", self.root / "trust.json"),
            (auth, "RECEIPTS", self.root / "receipts"),
            (taskstate, "TASK_ROOT", self.root / "tasks"),
            (audit, "LEDGER_PATH", self.root / "audit.jsonl"),
            (ra, "IMPLEMENTER_KEY_FILE", self.root / "implementer.key"),
        ]:
            self.stack.enter_context(patch.object(module, name, value))
        self.stack.enter_context(patch.object(ra, "_worktree_dirty", return_value=False))
        self.stack.enter_context(patch.object(ra, "_git", return_value="a" * 40))
        self.stack.enter_context(patch.object(evidence, "_git_sha", return_value="a" * 40))

        from aeris_runtime.blueprint_compatibility import TARGET
        self.core_target = TARGET

        # A real SUPERVISOR_STARTED event, since compute_version_tuple()
        # deliberately refuses to fabricate a started_at otherwise.
        audit.append_event("SUPERVISOR_STARTED", "AERIS Supervisor", {}, path=audit.LEDGER_PATH)

        self.human_key = bytes(range(64, 96))

    def _sign_human_g5(self, prepared):
        now = datetime.now(timezone.utc)
        payload = {
            **prepared["metadata"],
            "task_id": prepared["task_id"],
            "gate": "G5_APPROVAL",
            "decision": "PASS",
            "signer_id": "human-chief-engineer",
            "reviewer_context": "isolated-human-review-context",
            "issued_at": (now - timedelta(seconds=1)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "approval_action": "APPROVE_EXACT_ARTIFACT",
            "run_id": prepared["run_id"],
            "bundle_sha256": hashlib.sha256(
                (evidence.bundle_dir(prepared["run_id"]) / "bundle_manifest.json").read_bytes()
            ).hexdigest(),
        }
        receipt = {"payload": payload, "signature": hmac.new(self.human_key, auth.canonical(payload), hashlib.sha256).hexdigest()}
        (auth.RECEIPTS / "G5_APPROVAL.json").write_text(json.dumps(receipt), encoding="utf-8")
        trust = json.loads(auth.TRUST_STORE.read_text(encoding="utf-8"))
        trust["principals"]["human-chief-engineer"] = {
            "key_hex": self.human_key.hex(), "revoked": False,
            "subject_id": "the-real-human", "kind": "HUMAN",
            "human_authority": "Human Chief Engineer",
            "allowed_gates": ["G5_APPROVAL"],
            "isolated_contexts": ["isolated-human-review-context"],
        }
        auth.TRUST_STORE.write_text(json.dumps(trust), encoding="utf-8")

    def test_compute_version_tuple_refuses_without_a_supervisor_start_record(self):
        empty_ledger = self.root / "no-events.jsonl"
        with patch.object(audit, "LEDGER_PATH", empty_ledger):
            with self.assertRaisesRegex(ValueError, "SUPERVISOR_STARTED"):
                ra.compute_version_tuple()

    def test_compute_version_tuple_refuses_a_dirty_worktree(self):
        with patch.object(ra, "_worktree_dirty", return_value=True):
            with self.assertRaisesRegex(ValueError, "dirty"):
                ra.compute_version_tuple()

    def test_status_is_honestly_unaligned_before_any_setup(self):
        status = ra.current_release_authority_status()
        self.assertFalse(status["aligned"])
        self.assertEqual(status["reason"], "NO_RELEASE_AUTHORITY_TRUST_STORE_CONFIGURED")

    def test_status_is_honestly_unaligned_after_implementer_side_alone(self):
        ra.prepare_release_task()
        status = ra.current_release_authority_status()
        self.assertFalse(status["aligned"])
        self.assertEqual(status["reason"], "NO_HUMAN_G5_APPROVAL_RECEIPT_PRESENT")

    def test_prepared_task_resolves_once_a_real_human_g5_receipt_is_added(self):
        prepared = ra.prepare_release_task()
        self._sign_human_g5(prepared)
        status = ra.current_release_authority_status()
        self.assertTrue(status["aligned"], status.get("reason"))
        self.assertEqual(status["authority"]["reviewer_subject_id"], "the-real-human")
        self.assertEqual(status["authority"]["implementer_subject_id"], ra.IMPLEMENTER_SUBJECT_ID)

    def test_implementer_cannot_also_be_the_reviewer(self):
        """The AI-held implementer key must never be reusable as the G5
        reviewer key -- release_evidence.resolve() already rejects a
        subject/key collision; this confirms our own key never coincides."""
        prepared = ra.prepare_release_task()
        implementer_key = ra._implementer_key()
        self.assertNotEqual(implementer_key, self.human_key)
        # Signing G5 with the *implementer's own* key must be rejected.
        now = datetime.now(timezone.utc)
        payload = {
            **prepared["metadata"], "task_id": prepared["task_id"], "gate": "G5_APPROVAL",
            "decision": "PASS", "signer_id": ra.IMPLEMENTER_SIGNER_ID,
            "reviewer_context": "isolated-human-review-context",
            "issued_at": (now - timedelta(seconds=1)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "approval_action": "APPROVE_EXACT_ARTIFACT", "run_id": prepared["run_id"],
            "bundle_sha256": hashlib.sha256(
                (evidence.bundle_dir(prepared["run_id"]) / "bundle_manifest.json").read_bytes()
            ).hexdigest(),
        }
        trust = json.loads(auth.TRUST_STORE.read_text(encoding="utf-8"))
        trust["principals"][ra.IMPLEMENTER_SIGNER_ID]["allowed_gates"] = ["G5_APPROVAL"]
        trust["principals"][ra.IMPLEMENTER_SIGNER_ID]["human_authority"] = "Human Chief Engineer"
        trust["principals"][ra.IMPLEMENTER_SIGNER_ID]["isolated_contexts"] = ["isolated-human-review-context"]
        auth.TRUST_STORE.write_text(json.dumps(trust), encoding="utf-8")
        receipt = {"payload": payload, "signature": hmac.new(implementer_key, auth.canonical(payload), hashlib.sha256).hexdigest()}
        (auth.RECEIPTS / "G5_APPROVAL.json").write_text(json.dumps(receipt), encoding="utf-8")
        task = taskstate.load_task(prepared["task_id"])
        with self.assertRaisesRegex(ValueError, "collision"):
            auth.resolve("G5_APPROVAL", task, "G5_APPROVAL")


if __name__ == "__main__":
    unittest.main()
