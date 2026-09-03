import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def load_json(relative: str) -> dict:
    return json.loads(read(relative))


class TruthDocumentationTests(unittest.TestCase):
    def test_readme_exposes_two_url_default_without_claude_dependency(self):
        readme = read("README.md")
        self.assertIn("two URLs are the complete Full-Build trigger", readme)
        self.assertIn("Claude Code is optional", readme)
        self.assertIn("No Claude token is required", readme)
        self.assertNotIn("交給 Claude Code 獨立驗收", readme)
        self.assertNotIn("安裝/開幕後 Claude Code 自動檢查", readme)

    def test_reality_audit_cannot_redeclare_closed_p0_baselines_missing(self):
        audit = read("docs/AUDIT_REALITY_CHECK.md")
        self.assertIn("Core P0 trust foundation has executable TESTED baselines", audit)
        self.assertNotIn("Core P0 trust foundation is still missing", audit)
        self.assertNotIn("independent reviewer allocation;", audit)
        self.assertNotIn("Golden acoustic failure/regression cases;", audit)
        core_sha = load_json("core.lock.json")["baseline_sha"]
        self.assertIn(core_sha, audit)

    def test_baseline_and_full_scope_truth_are_separated(self):
        maturity = load_json("config/maturity.json")
        caps = maturity["capabilities"]
        expected_tested = (
            "100_role_contract_framework_baseline",
            "golden_acoustic_regression_baseline",
            "real_browser_semantic_e2e",
            "machine_resource_qualification_baseline",
            "zero_cost_no_claude_default_deployment",
        )
        for capability in expected_tested:
            self.assertEqual(caps[capability]["state"], "TESTED", capability)
            self.assertTrue(str(caps[capability].get("evidence", "")).strip(), capability)

        self.assertEqual(caps["100_role_executable_domain_contracts"]["state"], "HUMAN_GATE")
        self.assertEqual(caps["golden_acoustic_dataset_suite"]["state"], "PHYSICAL_HARDWARE")
        self.assertEqual(caps["browser_e2e_visual_regression"]["state"], "TESTED")
        self.assertEqual(caps["machine_resource_qualification"]["state"], "REBOOT_LOGOFF_REQUIRED")

    def test_company_and_baseline_snapshots_do_not_reintroduce_stale_closed_truth(self):
        company = load_json("company/company.manifest.json")
        trust = company["trust_baseline"]
        self.assertIn("TASK_AWARE_REVIEWER_ALLOCATION_TESTED_BASELINE", trust["independent_review"])
        self.assertIn("CLAUDE_OPTIONAL_NOT_DEFAULT", trust["independent_review"])
        self.assertIn("TESTED_REGRESSION_BASELINE_NOT_PRODUCTION_GOLDEN_DATASET", trust["golden_acoustic_cases"])
        self.assertNotIn("NOT_REVIEWER_ALLOCATION_ENGINE", trust["independent_review"])
        self.assertNotEqual(trust["golden_acoustic_cases"], "NOT_IMPLEMENTED")

        baselines = load_json("config/baseline_capabilities.v1.json")["capabilities"]
        browser = baselines["browser_visual_accessibility_baseline"]
        self.assertEqual(browser["state"], "TESTED")
        evidence_text = " ".join(browser["evidence"])
        self.assertNotIn("PR #24", evidence_text)
        self.assertNotIn("required before merge", browser["truth"].lower())
        self.assertIn("not cross-version pixel-golden regression", browser["truth"].lower())

    def test_reality_audit_preserves_external_and_real_machine_boundaries(self):
        audit = read("docs/AUDIT_REALITY_CHECK.md")
        for phrase in (
            "PRE_ALPHA",
            "real-machine acceptance",
            "production-complete Speaker/Microphone Golden Dataset",
            "EXTERNAL_LICENSE",
            "COMSOL",
            "MATLAB",
            "APx",
            "KLIPPEL",
            "SoundCheck",
            "ACQUA",
        ):
            self.assertIn(phrase, audit)


if __name__ == "__main__":
    unittest.main()
