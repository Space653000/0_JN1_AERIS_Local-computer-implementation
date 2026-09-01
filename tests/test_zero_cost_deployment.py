import unittest

from aeris_runtime.deployment_policy import load_policy, validate_default_deployment


class ZeroCostNoClaudeDeploymentTests(unittest.TestCase):
    def test_policy_explicitly_requires_no_paid_software_or_claude_token(self):
        policy = load_policy()
        self.assertFalse(policy["monetary_policy"]["paid_software_required"])
        self.assertFalse(policy["monetary_policy"]["paid_cloud_api_required"])
        self.assertFalse(policy["monetary_policy"]["auto_accept_license_or_eula"])
        self.assertFalse(policy["ai_policy"]["claude_code_required"])
        self.assertFalse(policy["ai_policy"]["claude_token_required"])
        self.assertFalse(policy["ai_policy"]["launch_claude_code"])
        self.assertEqual(policy["ai_policy"]["primary_executor"], "codex")

    def test_default_deployment_entrypoints_obey_policy(self):
        result = validate_default_deployment()
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse(result["claude_token_required"])
        self.assertFalse(result["paid_professional_software_required_for_default_opening"])

    def test_optional_paid_professional_adapters_stay_external_blockers(self):
        result = validate_default_deployment()
        checks = {item["check"]: item for item in result["checks"]}
        for capability in (
            "comsol_adapter",
            "matlab_adapter",
            "apx_adapter",
            "klippel_adapter",
            "soundcheck_adapter",
            "acqua_adapter",
        ):
            item = checks[f"external_capability:{capability}"]
            self.assertTrue(item["passed"], item)
            self.assertEqual(item["observed"], "BLOCKED_EXTERNAL")


if __name__ == "__main__":
    unittest.main()
