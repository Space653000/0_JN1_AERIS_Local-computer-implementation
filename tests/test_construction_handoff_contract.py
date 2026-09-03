import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "construction_handoff.v1.json"
PHASES = ROOT / "config" / "build_phases.v1.json"
DOC = ROOT / "docs" / "AERIS_CONSTRUCTION_SUPERVISION_LOOP.md"


class ConstructionHandoffContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_contract_is_draft_pr_only_and_core_read_only(self):
        self.assertEqual(self.data["schema_version"], 1)
        self.assertEqual(self.data["contract_id"], "AERIS-CONSTRUCTION-SUPERVISION-HANDOFF-V1")
        self.assertEqual(self.data["default_mode"], "LOCAL_BUILD_NO_PUSH")
        self.assertEqual(self.data["handoff_mode"], "DRAFT_PR_REVIEW_ONLY")
        rules = self.data["rules"]
        self.assertTrue(rules["core_read_only"])
        self.assertTrue(rules["never_push_core"])
        self.assertTrue(rules["never_push_directly_to_main"])
        self.assertTrue(rules["require_non_main_review_branch"])
        self.assertTrue(rules["require_draft_pull_request"])
        self.assertTrue(rules["do_not_merge_during_handoff"])

    def test_snapshot_contract_covers_review_truth(self):
        required = set(self.data["snapshot_required_fields"])
        expected = {
            "handoff_id",
            "phase_id",
            "remote_main_sha_at_handoff",
            "local_commit_sha",
            "merge_base_sha",
            "changed_files",
            "maturity_counts",
            "executable_skill_count",
            "method_count",
            "golden_case_count",
            "negative_case_count",
            "regression_case_count",
            "test_summary",
            "unresolved_capability_gaps",
            "external_or_human_gates",
            "excluded_local_only_artifacts",
            "evidence_manifest",
            "review_request",
        }
        self.assertTrue(expected.issubset(required))

    def test_privacy_screen_is_mandatory(self):
        self.assertTrue(self.data["rules"]["require_privacy_secret_screen_before_push"])
        patterns = self.data["never_push_patterns"]
        self.assertIn(".env", patterns)
        self.assertIn(".aeris/**/*.db", patterns)
        self.assertIn("user_measurements/**", patterns)
        self.assertIn("customer_data/**", patterns)

    def test_phase_catalog_links_supervision_contract(self):
        phases = json.loads(PHASES.read_text(encoding="utf-8"))
        self.assertEqual(phases["supervision_handoff_contract"], "config/construction_handoff.v1.json")
        self.assertTrue(DOC.is_file())

    def test_handoff_does_not_claim_completion(self):
        truth = self.data["truth_boundary"]
        self.assertIn("reviewable", truth["draft_pr_means"])
        self.assertIn("phase complete", truth["draft_pr_does_not_mean"])
        self.assertIn("real evidence", truth["l4_requires"])

    def test_handoff_ids_are_monotonic_unique_and_never_reused(self):
        rules = self.data["rules"]
        numbering = self.data["numbering"]
        self.assertTrue(rules["never_reuse_handoff_id"])
        self.assertTrue(rules["new_supervisor_prompt_requires_new_handoff_id"])
        self.assertTrue(rules["new_handoff_requires_new_branch_and_new_pr"])
        self.assertTrue(rules["previous_handoff_pr_must_not_be_overwritten"])
        self.assertEqual(numbering["handoff_id_format"], "H%04d")
        self.assertEqual(numbering["first_handoff_id"], "H0001")
        self.assertEqual(numbering["sequence_scope"], "repository_global")
        self.assertTrue(numbering["sequence_is_monotonic"])
        self.assertFalse(numbering["reuse_closed_or_abandoned_ids"])
        self.assertIn("max+1", numbering["supervisor_allocation_rule"])
        self.assertIn("collision", numbering["codex_collision_rule"].lower())
        self.assertIn("{handoff_id}", numbering["branch_template"])
        self.assertIn("{handoff_id}", numbering["directory_template"])
        self.assertIn("{handoff_id}", numbering["pr_title_template"])
        self.assertIn("{handoff_id}", numbering["ready_signal_template"])

    def test_supervision_doc_forbids_repurposing_previous_pr(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("H0001", text)
        self.assertIn("H0002", text)
        self.assertIn("never reused", text)
        self.assertIn("new Draft PR", text)
        self.assertIn("previous Draft PR remains unchanged", text)


if __name__ == "__main__":
    unittest.main()
