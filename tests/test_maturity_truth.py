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

    def test_tested_baselines_cannot_remain_stale_not_implemented_in_maturity(self):
        maturity = load_json("config/maturity.json")
        baselines = load_json("config/baseline_capabilities.v1.json")["capabilities"]

        reviewer_baseline = baselines["task_aware_independent_reviewer_allocation_baseline"]
        self.assertEqual(reviewer_baseline["state"], "TESTED")
        reviewer_maturity = maturity["capabilities"]["independent_reviewer_allocation_engine"]
        self.assertEqual(reviewer_maturity["state"], "TESTED")
        self.assertTrue(str(reviewer_maturity.get("evidence", "")).strip())
        self.assertIn("allocation is not proof", reviewer_maturity.get("note", "").lower())

        role_baseline = baselines["role_contract_framework_baseline"]
        self.assertEqual(role_baseline["state"], "TESTED")
        full_role_maturity = maturity["capabilities"]["100_role_executable_domain_contracts"]
        self.assertEqual(full_role_maturity["state"], "NOT_IMPLEMENTED")

        machine_baseline = baselines["machine_resource_qualification_engine_baseline"]
        self.assertEqual(machine_baseline["state"], "TESTED")
        full_machine_maturity = maturity["capabilities"]["machine_resource_qualification"]
        self.assertEqual(full_machine_maturity["state"], "NOT_IMPLEMENTED")

        golden_baseline = baselines["golden_acoustic_regression_baseline"]
        self.assertEqual(golden_baseline["state"], "TESTED")
        full_golden_maturity = maturity["capabilities"]["golden_acoustic_dataset_suite"]
        self.assertEqual(full_golden_maturity["state"], "NOT_IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
