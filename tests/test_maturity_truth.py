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
            if item["state"] in {"NOT_IMPLEMENTED", "BLOCKED_EXTERNAL", "HUMAN_GATE", "EXTERNAL_LICENSE", "PHYSICAL_HARDWARE", "REBOOT_LOGOFF_REQUIRED"}:
                self.assertNotEqual(item["state"], "VERIFIED", name)
        self.assertFalse(any(item["state"] == "NOT_IMPLEMENTED" for item in maturity["capabilities"].values()))

    def test_reviewer_allocator_truth_matches_tested_implementation(self):
        maturity = load_json("config/maturity.json")
        reviewer = maturity["capabilities"]["independent_reviewer_allocation_engine"]
        self.assertEqual(reviewer["state"], "TESTED")
        evidence = str(reviewer.get("evidence", "")).lower()
        self.assertIn("reviewer", evidence)
        self.assertIn("test", evidence)

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


if __name__ == "__main__":
    unittest.main()
