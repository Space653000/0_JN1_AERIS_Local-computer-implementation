import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "build_phases.v1.json"
DOC_INDEX = ROOT / "docs" / "AERIS_BUILD_PHASES.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"


class BuildPhaseContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_catalog_is_machine_readable_and_ordered(self):
        self.assertEqual(self.data["schema_version"], 1)
        self.assertEqual(self.data["contract_id"], "AERIS-PERSISTENT-BUILD-PHASES-V1")
        phases = self.data["phases"]
        self.assertGreaterEqual(len(phases), 2)
        ids = [phase["id"] for phase in phases]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_phase_spec_exists(self):
        for phase in self.data["phases"]:
            path = ROOT / phase["spec"]
            self.assertTrue(path.is_file(), f"missing build phase spec: {phase['spec']}")
            self.assertTrue(phase["primary_stop_condition"].strip())
            self.assertTrue(phase["completion_truth"].strip())

    def test_resume_policy_prevents_chat_history_rebuilds(self):
        policy = self.data["resume_policy"]
        self.assertTrue(policy["read_phase_catalog_on_two_url_trigger"])
        self.assertTrue(policy["inspect_local_evidence_before_execution"])
        self.assertTrue(policy["skip_satisfied_phases"])
        self.assertTrue(policy["rerun_only_if_evidence_missing_stale_invalid_or_incompatible"])
        self.assertTrue(policy["continue_automatically_to_next_unsatisfied_phase"])
        self.assertTrue(policy["never_use_chat_prose_as_completion_evidence"])
        self.assertTrue(policy["never_modify_canonical_core"])

    def test_human_and_agent_indexes_reference_persistent_catalog(self):
        doc_index = DOC_INDEX.read_text(encoding="utf-8")
        agents = AGENTS.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        for phase in self.data["phases"]:
            self.assertIn(phase["spec"], doc_index)
        self.assertIn("config/build_phases.v1.json", agents)
        self.assertIn("docs/AERIS_BUILD_PHASES.md", agents)
        self.assertIn("config/build_phases.v1.json", readme)
        self.assertIn("docs/AERIS_BUILD_PHASES.md", readme)

    def test_future_phase_policy_is_persistent(self):
        future = self.data["future_phase_policy"]
        self.assertTrue(future["persist_every_major_build_prompt_as_repo_spec"])
        self.assertTrue(future["append_to_this_machine_readable_catalog"])
        self.assertTrue(future["preserve_core_read_only_and_evidence_truth_rules"])
        self.assertTrue(future["require_normal_implementation_pr_ci_governance"])


if __name__ == "__main__":
    unittest.main()
