import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class QualityGateContractTests(unittest.TestCase):
    def test_permanent_regression_assets_exist(self):
        required = [
            "docs/AI_CHANGE_ACCEPTANCE_PROTOCOL.md",
            "scripts/windows-python-resolution.ps1",
            "tests/windows/test-python-resolution.ps1",
            "tests/test_maturity_truth.py",
            "config/pre_codex_gate.v1.json",
            "tests/test_pre_codex_gate.py",
            "aeris_runtime/claim_guard.py",
            "tests/test_claim_guard.py",
            "tests/browser_e2e.py",
            "tests/browser_visual_accessibility.py",
            "docs/BROWSER_VISUAL_ACCESSIBILITY_BASELINE.md",
            ".gitattributes",
            "config/machine_qualification.v1.json",
            "aeris_runtime/machine_qualification.py",
            "tests/test_machine_qualification.py",
            "golden/acoustics/v1/manifest.json",
            "aeris_runtime/golden_acoustics.py",
            "tests/test_golden_acoustics.py",
            "config/role_contracts.v1.json",
            "aeris_runtime/role_contracts.py",
            "aeris_runtime/reviewer_allocation.py",
            "tests/test_role_contracts.py",
            "tests/test_reviewer_allocation.py",
            "config/zero_cost_no_claude.v1.json",
            "aeris_runtime/deployment_policy.py",
            "tests/test_zero_cost_deployment.py",
            "scripts/windows-zero-cost-bootstrap.ps1",
            "tests/windows/test-zero-cost-bootstrap.ps1",
            "docs/ZERO_COST_NO_CLAUDE_DEPLOYMENT.md",
            "INSTALL_AERIS_LOCAL.ps1",
            "AERIS_AUTOPILOT.ps1",
            ".github/workflows/ci.yml",
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), f"required quality gate missing: {relative}")

    def test_ci_keeps_platform_and_regression_gates(self):
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        required_snippets = [
            "ubuntu-24.04",
            "windows-2025",
            "Parse every tracked PowerShell file",
            "Windows Python resolver Store-alias regression",
            "Windows zero-cost winget fail-closed regression",
            "Pre-Codex cloud contract gate",
            "Machine qualification and Golden acoustic baseline gate",
            "Role contract and independent reviewer allocation gate",
            "Zero-cost no-Claude default deployment gate",
            "Real browser semantic E2E for Dashboard Workspace Services",
            "Browser screenshot repeatability and accessibility baseline",
            "Windows one-click installer smoke without external runtime installation",
            "Windows full Autopilot entrypoint CI smoke",
            "Verify canonical Core has not drifted",
            "python -m unittest discover -s tests -v",
        ]
        for snippet in required_snippets:
            self.assertIn(snippet, ci, f"required CI gate missing/weakened: {snippet}")

    def test_browser_e2e_scope_cannot_be_upgraded_to_fake_visual_regression(self):
        text = (ROOT / "tests/browser_e2e.py").read_text(encoding="utf-8")
        visual = (ROOT / "tests/browser_visual_accessibility.py").read_text(encoding="utf-8")
        docs = (ROOT / "docs/BROWSER_VISUAL_ACCESSIBILITY_BASELINE.md").read_text(encoding="utf-8")
        self.assertIn("real headless browser SPA route/render semantic E2E; NOT pixel visual regression", text)
        self.assertIn('id=\"workspace\" class=\"view active-view\"', text)
        self.assertIn('id=\"services\" class=\"view active-view\"', text)
        self.assertIn("NOT cross-version pixel-golden regression", visual)
        self.assertIn("**not** a cross-version pixel-golden visual regression suite", docs.lower())

    def test_browser_accessibility_markers_are_permanent(self):
        html = (ROOT / "ui/web/index.html").read_text(encoding="utf-8")
        for marker in (
            'aria-label="AERIS 主要導覽"',
            'aria-label="儀表板"',
            'aria-label="工作區"',
            'aria-label="服務"',
            'role="status"',
            'aria-live="polite"',
            '<main id="mainContent">',
            '<label for="projectSelect">',
            '<label for="taskTitle">',
            '<label for="taskDescription">',
            '<label for="riskLevel">',
            '<label for="invokePrompt">',
        ):
            self.assertIn(marker, html)

    def test_machine_and_golden_baselines_cannot_be_upgraded_to_fake_verification(self):
        machine = (ROOT / "aeris_runtime/machine_qualification.py").read_text(encoding="utf-8")
        golden = (ROOT / "golden/acoustics/v1/manifest.json").read_text(encoding="utf-8")
        attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("not real-machine VERIFIED", machine)
        self.assertIn("not a production-complete speaker/microphone Golden Dataset", golden)
        self.assertIn("golden/acoustics/v1/*.csv text eol=lf", attrs)

    def test_role_contract_and_reviewer_baselines_cannot_fake_100_verified_engineers(self):
        contracts = (ROOT / "aeris_runtime/role_contracts.py").read_text(encoding="utf-8")
        allocation = (ROOT / "aeris_runtime/reviewer_allocation.py").read_text(encoding="utf-8")
        self.assertIn("do not mean 100 domain-verified engineers", contracts)
        self.assertIn("same_context_repair_and_approval_forbidden", allocation)
        self.assertIn("launch_external_model_by_default", allocation)
        self.assertIn('"Human Chief Engineer" if human_required else None', allocation)

    def test_zero_cost_no_claude_default_cannot_silently_regress(self):
        policy = (ROOT / "config/zero_cost_no_claude.v1.json").read_text(encoding="utf-8")
        validator = (ROOT / "aeris_runtime/deployment_policy.py").read_text(encoding="utf-8")
        installer = (ROOT / "scripts/one-click-install.ps1").read_text(encoding="utf-8")
        helper = (ROOT / "scripts/windows-zero-cost-bootstrap.ps1").read_text(encoding="utf-8")
        autopilot = (ROOT / "config/autopilot.json").read_text(encoding="utf-8")
        self.assertIn('"claude_token_required": false', policy)
        self.assertIn('"paid_software_required": false', policy)
        self.assertIn("FORBIDDEN_DEFAULT_INSTALLER_TOKEN", validator)
        self.assertIn("windows-zero-cost-bootstrap.ps1", installer)
        self.assertIn("Install-WingetPackageNoAgreement", helper)
        self.assertIn("--disable-interactivity", helper)
        self.assertIn('"deployment_profile": "AERIS-ZERO-COST-NO-CLAUDE-V1"', autopilot)

    def test_windows_resolver_contract_is_not_reverted(self):
        resolver = (ROOT / "scripts/windows-python-resolution.ps1").read_text(encoding="utf-8")
        installer = (ROOT / "scripts/one-click-install.ps1").read_text(encoding="utf-8")
        self.assertIn("@('-3.11','-3')", resolver)
        self.assertIn("Test-AerisPythonExecutable", resolver)
        self.assertIn("Generic `python` is deliberately late", resolver)
        self.assertIn("windows-python-resolution.ps1", installer)
        self.assertIn("Resolve-AerisPython", installer)

    def test_model_measurement_hallucination_guard_cannot_silently_disappear(self):
        guard = (ROOT / "aeris_runtime/claim_guard.py").read_text(encoding="utf-8")
        roles = (ROOT / "aeris_runtime/roles.py").read_text(encoding="utf-8")
        regression = (ROOT / "tests/test_claim_guard.py").read_text(encoding="utf-8")
        self.assertIn("REJECTED_UNSUPPORTED_OR_INVALID_CLAIM", guard)
        self.assertIn("uses measured/verified-fact wording without EVIDENCE classification", guard)
        self.assertIn("AERIS_ROLE_EVIDENCE_SCHEMA_V1", roles)
        self.assertIn("已有量測記錄證明此單體通過測試", regression)

    def test_ai_protocol_requires_post_merge_main_ci(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        protocol = (ROOT / "docs/AI_CHANGE_ACCEPTANCE_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("verify merged main Windows + Ubuntu CI", agents)
        self.assertIn("post-merge main CI", protocol)
        self.assertIn("Regression tests are permanent evidence", protocol)
        self.assertIn("Cross-file truth changes are atomic", protocol)


if __name__ == "__main__":
    unittest.main()
