import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MaturityTruthTests(unittest.TestCase):
    def test_maturity_states_are_valid_and_evidence_backed(self):
        maturity = json.loads((ROOT / "config" / "maturity.json").read_text(encoding="utf-8"))
        allowed = set(maturity["states"])
        for name, item in maturity["capabilities"].items():
            self.assertIn(item["state"], allowed, name)
            if item["state"] in {"TESTED", "VERIFIED"}:
                self.assertTrue(str(item.get("evidence", "")).strip(), f"{name} lacks evidence reference")
            if item["state"] in {"NOT_IMPLEMENTED", "BLOCKED_EXTERNAL"}:
                self.assertNotEqual(item["state"], "VERIFIED", name)

    def test_product_stage_matches_company_manifest(self):
        maturity = json.loads((ROOT / "config" / "maturity.json").read_text(encoding="utf-8"))
        company = json.loads((ROOT / "company" / "company.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(maturity["product_stage"], company["product_stage"])

    def test_no_complete_claim_in_pre_alpha_manifest(self):
        company = json.loads((ROOT / "company" / "company.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(company["product_stage"], "PRE_ALPHA")
        self.assertNotEqual(company["organization"]["role_maturity"], "VERIFIED_100_ENGINEERS")


if __name__ == "__main__":
    unittest.main()
