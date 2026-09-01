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
            "Windows one-click installer smoke without external runtime installation",
            "Windows full Autopilot entrypoint CI smoke",
            "Verify canonical Core has not drifted",
            "python -m unittest discover -s tests -v",
        ]
        for snippet in required_snippets:
            self.assertIn(snippet, ci, f"required CI gate missing/weakened: {snippet}")

    def test_windows_resolver_contract_is_not_reverted(self):
        resolver = (ROOT / "scripts/windows-python-resolution.ps1").read_text(encoding="utf-8")
        installer = (ROOT / "scripts/one-click-install.ps1").read_text(encoding="utf-8")
        self.assertIn("@('-3.11','-3')", resolver)
        self.assertIn("Test-AerisPythonExecutable", resolver)
        self.assertIn("Generic `python` is deliberately late", resolver)
        self.assertIn("windows-python-resolution.ps1", installer)
        self.assertIn("Resolve-AerisPython", installer)

    def test_ai_protocol_requires_post_merge_main_ci(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        protocol = (ROOT / "docs/AI_CHANGE_ACCEPTANCE_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("verify merged main Windows + Ubuntu CI", agents)
        self.assertIn("post-merge main CI", protocol)
        self.assertIn("Regression tests are permanent evidence", protocol)
        self.assertIn("Cross-file truth changes are atomic", protocol)


if __name__ == "__main__":
    unittest.main()
