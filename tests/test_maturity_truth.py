import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


class MaturityTruthTests(unittest.TestCase):
    def test_maturity_states_are_valid_and_evidence_backed(self):
        maturity = load_json("config/maturity.json")
        allowed = set(maturity["states"])
        for name, item in maturity["capabilities"].items():
            self.assertIn(item["state"], allowed, name)
            if item["state"] in {"TESTED", "VERIFIED"}:
                self.assertTrue(str(item.get("evidence", "")).strip(), f"{name} lacks evidence reference")
            if item["state"] in {"NOT_IMPLEMENTED", "BLOCKED_EXTERNAL"}:
                self.assertNotEqual(item["state"], "VERIFIED", name)

    def test_product_stage_matches_company_manifest(self):
        maturity = load_json("config/maturity.json")
        company = load_json("company/company.manifest.json")
        self.assertEqual(maturity["product_stage"], company["product_stage"])

    def test_no_complete_claim_in_pre_alpha_manifest(self):
        company = load_json("company/company.manifest.json")
        self.assertEqual(company["product_stage"], "PRE_ALPHA")
        self.assertNotEqual(company["organization"]["role_maturity"], "VERIFIED_100_ENGINEERS")

    def test_canonical_core_sha_is_identical_across_all_tracked_truth_contracts(self):
        maturity = load_json("config/maturity.json")
        lock = load_json("core.lock.json")
        alignment = load_json("config/core_alignment.json")
        autopilot = load_json("config/autopilot.json")
        company = load_json("company/company.manifest.json")

        expected = lock["baseline_sha"]
        observed = {
            "maturity.evidence_snapshot.canonical_core_reviewed_sha": maturity["evidence_snapshot"]["canonical_core_reviewed_sha"],
            "core_alignment.canonical_core.reviewed_sha": alignment["canonical_core"]["reviewed_sha"],
            "autopilot.canonical_core_sha": autopilot["canonical_core_sha"],
            "company.core_target.reviewed_sha": company["core_target"]["reviewed_sha"],
        }
        for source, sha in observed.items():
            self.assertEqual(sha, expected, f"Core truth drift at {source}: {sha} != {expected}")

    def test_reviewer_allocator_maturity_matches_tested_baseline(self):
        maturity = load_json("config/maturity.json")
        baselines = load_json("config/baseline_capabilities.v1.json")
        mature = maturity["capabilities"]["independent_reviewer_allocation_engine"]
        baseline = baselines["capabilities"]["task_aware_independent_reviewer_allocation_baseline"]
        self.assertEqual(baseline["state"], "TESTED")
        self.assertEqual(mature["state"], "TESTED")
        self.assertIn("reviewer_allocation.py", mature["evidence"])
        self.assertIn("does not require Claude", mature["note"])

    def test_full_domain_and_physical_scopes_remain_truthfully_incomplete(self):
        maturity = load_json("config/maturity.json")
        capabilities = maturity["capabilities"]
        for name in (
            "100_role_executable_domain_contracts",
            "golden_acoustic_dataset_suite",
            "full_skills_library",
            "full_methods_library",
            "browser_e2e_visual_regression",
            "machine_resource_qualification",
            "release_signing_and_attestation",
            "commercial_release_readiness",
        ):
            self.assertEqual(capabilities[name]["state"], "NOT_IMPLEMENTED", name)
        for name in ("comsol_adapter", "matlab_adapter", "apx_adapter", "klippel_adapter", "soundcheck_adapter", "acqua_adapter"):
            self.assertEqual(capabilities[name]["state"], "BLOCKED_EXTERNAL", name)


if __name__ == "__main__":
    unittest.main()
