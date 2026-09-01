import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CoreAlignmentTests(unittest.TestCase):
    def test_alignment_contract_is_tied_to_core_lock(self):
        alignment = json.loads((ROOT / "config" / "core_alignment.json").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "core.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(alignment["canonical_core"]["reviewed_sha"], lock["baseline_sha"])
        self.assertEqual(alignment["canonical_core"]["repository"], "Space653000/0_JN1_AERIS")

    def test_company_manifest_preserves_core_pod_ranges(self):
        alignment = json.loads((ROOT / "config" / "core_alignment.json").read_text(encoding="utf-8"))
        company = json.loads((ROOT / "company" / "company.manifest.json").read_text(encoding="utf-8"))
        target = company["organization"]["runtime_active_role_target"]
        self.assertEqual(
            [target["ordinary_task"]["min"], target["ordinary_task"]["max"]],
            alignment["non_negotiable_invariants"]["pod_targets"]["ordinary_task"],
        )
        self.assertEqual(
            [target["complex_task"]["min"], target["complex_task"]["max"]],
            alignment["non_negotiable_invariants"]["pod_targets"]["complex_task"],
        )
        self.assertTrue(target["not_100_persistent_processes"])

    def test_implementation_constitution_keeps_mic_validation_axes(self):
        alignment = json.loads((ROOT / "config" / "core_alignment.json").read_text(encoding="utf-8"))
        constitution = (ROOT / "company" / "CONSTITUTION.md").read_text(encoding="utf-8").lower()
        for axis in alignment["non_negotiable_invariants"]["mic_algorithm_validation_axes"]:
            self.assertIn(axis.lower(), constitution, f"missing Core-required mic validation axis: {axis}")

    def test_truth_invariants_are_not_reversed(self):
        alignment = json.loads((ROOT / "config" / "core_alignment.json").read_text(encoding="utf-8"))
        inv = alignment["non_negotiable_invariants"]
        self.assertFalse(inv["model_is_identity"])
        self.assertFalse(inv["memory_is_evidence"])
        self.assertFalse(inv["execution_is_completion"])
        self.assertFalse(inv["agent_consensus_establishes_engineering_truth"])
        self.assertTrue(inv["independent_verification_required_for_formal_completion"])
        self.assertFalse(inv["core_is_writable_by_codex_or_implementation"])


if __name__ == "__main__":
    unittest.main()
