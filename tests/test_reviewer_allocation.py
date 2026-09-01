import unittest

from aeris_runtime.reviewer_allocation import allocate_reviewers


class ReviewerAllocationTests(unittest.TestCase):
    def test_r0_requires_no_independent_reviewer(self):
        result = allocate_reviewers("R009", "R0")
        self.assertFalse(result["independent_review_required"])
        self.assertEqual(result["reviewer_count"], 0)
        self.assertFalse(result["human_approval_required"])

    def test_r2_allocates_independent_separated_reviewer(self):
        result = allocate_reviewers("R009", "R2")
        self.assertTrue(result["independent_review_required"])
        self.assertEqual(result["reviewer_count"], 1)
        reviewer = result["reviewers"][0]
        self.assertNotEqual(reviewer["role_id"], "R009")
        self.assertEqual(reviewer["context_policy"], "FRESH_REVIEW_CONTEXT_REQUIRED")
        self.assertIn("repair_same_change", reviewer["forbidden_permissions"])
        self.assertFalse(result["launch_external_model_by_default"])

    def test_primary_red_team_role_gets_different_reviewer(self):
        result = allocate_reviewers("R098", "R2")
        self.assertNotEqual(result["reviewers"][0]["role_id"], "R098")

    def test_r3_r4_preserve_human_chief_engineer_authority(self):
        for risk in ("R3", "R4"):
            result = allocate_reviewers("R009", risk)
            self.assertEqual(result["reviewer_count"], 2)
            self.assertTrue(result["human_approval_required"])
            self.assertEqual(result["human_authority"], "Human Chief Engineer")
            self.assertEqual(len({item["role_id"] for item in result["reviewers"]}), 2)

    def test_unknown_risk_fails_closed(self):
        with self.assertRaises(ValueError):
            allocate_reviewers("R009", "R9")


if __name__ == "__main__":
    unittest.main()
