import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


class PreCodexCloudGateTests(unittest.TestCase):
    def test_default_path_is_zero_cost_no_claude_and_fail_closed(self):
        gate = load("config/pre_codex_gate.v1.json")
        zero = load("config/zero_cost_no_claude.v1.json")
        autopilot = load("config/autopilot.json")
        self.assertEqual(gate["gate_id"], "AERIS-PRE-CODEX-CLOUD-GATE-V1")
        self.assertTrue(gate["required"]["paid_professional_tools_not_required"])
        self.assertTrue(gate["required"]["claude_code_or_token_not_required"])
        self.assertTrue(gate["required"]["no_auto_accept_license_or_eula"])
        self.assertFalse(zero["monetary_policy"]["paid_software_required"])
        self.assertFalse(zero["monetary_policy"]["paid_cloud_api_required"])
        self.assertFalse(zero["monetary_policy"]["auto_accept_license_or_eula"])
        self.assertFalse(zero["ai_policy"]["claude_code_required"])
        self.assertFalse(zero["ai_policy"]["claude_token_required"])
        defaults = autopilot["default_execution_policy"]
        self.assertFalse(defaults["launch_claude_code"])
        self.assertFalse(defaults["launch_second_model_reviewer"])
        self.assertFalse(defaults["require_claude_token"])
        self.assertFalse(defaults["install_paid_software"])
        self.assertFalse(defaults["auto_accept_license_or_eula"])

    def test_core_truth_is_atomic(self):
        expected = load("core.lock.json")["baseline_sha"]
        self.assertEqual(load("config/core_alignment.json")["canonical_core"]["reviewed_sha"], expected)
        self.assertEqual(load("config/autopilot.json")["canonical_core_sha"], expected)
        self.assertEqual(load("company/company.manifest.json")["core_target"]["reviewed_sha"], expected)
        self.assertEqual(load("config/maturity.json")["evidence_snapshot"]["canonical_core_reviewed_sha"], expected)

    def test_tested_baseline_truth_does_not_regress_or_overclaim_full_maturity(self):
        baselines = load("config/baseline_capabilities.v1.json")["capabilities"]
        maturity = load("config/maturity.json")["capabilities"]
        self.assertEqual(baselines["task_aware_independent_reviewer_allocation_baseline"]["state"], "TESTED")
        self.assertEqual(maturity["independent_reviewer_allocation_engine"]["state"], "TESTED")
        self.assertEqual(baselines["machine_resource_qualification_engine_baseline"]["state"], "TESTED")
        self.assertEqual(maturity["machine_resource_qualification_baseline"]["state"], "TESTED")
        self.assertEqual(maturity["machine_resource_qualification"]["state"], "NOT_IMPLEMENTED")
        self.assertEqual(baselines["golden_acoustic_regression_baseline"]["state"], "TESTED")
        self.assertEqual(maturity["golden_acoustic_regression_baseline"]["state"], "TESTED")
        self.assertEqual(maturity["golden_acoustic_dataset_suite"]["state"], "NOT_IMPLEMENTED")
        self.assertEqual(baselines["role_contract_framework_baseline"]["state"], "TESTED")
        self.assertEqual(maturity["100_role_contract_framework_baseline"]["state"], "TESTED")
        self.assertEqual(maturity["100_role_executable_domain_contracts"]["state"], "NOT_IMPLEMENTED")
        self.assertEqual(baselines["zero_cost_no_claude_default_deployment_policy"]["state"], "TESTED")
        self.assertEqual(maturity["zero_cost_no_claude_default_deployment"]["state"], "TESTED")
        self.assertEqual(baselines["browser_visual_accessibility_baseline"]["state"], "TESTED")
        self.assertEqual(maturity["real_browser_semantic_e2e"]["state"], "TESTED")
        self.assertEqual(maturity["browser_e2e_visual_regression"]["state"], "NOT_IMPLEMENTED")

    def test_pre_codex_gate_never_means_product_complete(self):
        gate = load("config/pre_codex_gate.v1.json")
        maturity = load("config/maturity.json")
        company = load("company/company.manifest.json")
        self.assertEqual(maturity["product_stage"], "PRE_ALPHA")
        self.assertFalse(company.get("company_complete", False))
        truth = gate["truth"].lower()
        self.assertIn("does not mean", truth)
        self.assertIn("real-machine", truth)


if __name__ == "__main__":
    unittest.main()
