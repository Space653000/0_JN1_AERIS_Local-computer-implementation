import unittest

from aeris_runtime.role_contracts import coverage_report, get_contract, materialize_contracts


class RoleContractFrameworkTests(unittest.TestCase):
    def test_exactly_100_unique_structurally_valid_contracts(self):
        contracts = materialize_contracts()
        self.assertEqual(len(contracts), 100)
        self.assertEqual(len({item["role_id"] for item in contracts}), 100)
        self.assertTrue(all(item["asset_integrity"]["valid"] for item in contracts))
        self.assertTrue(all(len(item["contract_sha256"]) == 64 for item in contracts))

    def test_every_contract_keeps_domain_gap_truthful(self):
        contracts = materialize_contracts()
        self.assertTrue(all(item["execution_state"] == "CONTRACTED_BASELINE_NOT_DOMAIN_VERIFIED" for item in contracts))
        self.assertTrue(all(item["domain_asset_gap"] is True for item in contracts))
        self.assertTrue(all(item["domain_verified"] is False for item in contracts))

    def test_referenced_standard_metadata_is_not_promoted_to_live_verified(self):
        speaker = get_contract(9)
        checks = [item for item in speaker["asset_integrity"]["checks"] if item["type"] == "standard_metadata"]
        self.assertTrue(checks)
        self.assertTrue(all(item["exists"] for item in checks))
        self.assertTrue(all(item["verification_state"] != "LIVE_VERIFIED" for item in checks))
        self.assertFalse(speaker["asset_integrity"]["standards_formally_live_verified"])

    def test_high_touch_roles_are_capped_at_r2_not_self_release(self):
        instrument = next(item for item in materialize_contracts() if item["role_name"] == "Laboratory Instrument Controller")
        certification = next(item for item in materialize_contracts() if item["role_name"] == "OEM / Customer Certification Engineer")
        self.assertEqual(instrument["risk_ceiling_without_human_gate"], "R2")
        self.assertEqual(certification["risk_ceiling_without_human_gate"], "R2")
        self.assertIn("self_approve_r3_r4", instrument["forbidden_actions"])

    def test_coverage_report_never_turns_100_contracts_into_100_verified_engineers(self):
        report = coverage_report()
        self.assertTrue(report["all_100_contracts_structurally_valid"])
        self.assertEqual(report["contracted_baseline_count"], 100)
        self.assertEqual(report["domain_verified_count"], 0)
        self.assertEqual(report["roles_with_domain_asset_gaps"], 100)
        self.assertIn("do not mean 100 domain-verified engineers", report["truth"])


if __name__ == "__main__":
    unittest.main()
