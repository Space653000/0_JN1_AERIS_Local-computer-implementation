import unittest

from aeris_runtime.reviewer_allocation import allocate_reviewers


class ReviewerAllocationTests(unittest.TestCase):
    def test_r0_requires_no_independent_reviewer(self):
        result = allocate_reviewers("R009", "R0")
        self.assertFalse(result["independent_review_required"])
        self.assertEqual(result["reviewer_count"], 0)
        self.assertFalse(result["human_approval_required"])
        self.assertFalse(result["claude_required"])

    def test_r2_allocates_independent_separated_reviewer(self):
        result = allocate_reviewers("R009", "R2", task_context="speaker measurement validation")
        self.assertTrue(result["independent_review_required"])
        self.assertEqual(result["reviewer_count"], 1)
        reviewer = result["reviewers"][0]
        self.assertNotEqual(reviewer["role_id"], "R009")
        self.assertEqual(reviewer["context_policy"], "FRESH_REVIEW_CONTEXT_REQUIRED")
        self.assertIn("repair_same_change", reviewer["forbidden_permissions"])
        self.assertFalse(result["launch_external_model_by_default"])
        self.assertTrue(result["task_context_provided"])
        self.assertEqual(len(result["task_context_sha256"]), 64)

    def test_standards_task_prefers_standards_reviewer(self):
        result = allocate_reviewers(
            "R009",
            "R2",
            task_context="Verify IEC 60268-5 standard applicability and current regulation evidence",
            task_tags=["standards", "speaker"],
        )
        reviewer = result["reviewers"][0]
        self.assertEqual(reviewer["role_id"], "R089")
        self.assertEqual(reviewer["review_specialty"], "standards")

    def test_requirements_task_prefers_requirements_reviewer(self):
        result = allocate_reviewers(
            "R027",
            "R2",
            task_context="customer specification requirement traceability configuration review",
        )
        self.assertEqual(result["reviewers"][0]["role_id"], "R097")

    def test_primary_red_team_role_gets_different_reviewer(self):
        result = allocate_reviewers("R098", "R2", task_context="DFMEA failure risk review")
        self.assertNotEqual(result["reviewers"][0]["role_id"], "R098")

    def test_r3_r4_preserve_human_chief_engineer_authority(self):
        for risk in ("R3", "R4"):
            result = allocate_reviewers("R009", risk, task_context="formal release risk and evidence")
            self.assertEqual(result["reviewer_count"], 2)
            self.assertTrue(result["human_approval_required"])
            self.assertEqual(result["human_authority"], "Human Chief Engineer")
            self.assertEqual(len({item["role_id"] for item in result["reviewers"]}), 2)

    def test_empty_task_context_has_deterministic_fallback(self):
        a = allocate_reviewers("R009", "R2")
        b = allocate_reviewers("R009", "R2")
        self.assertEqual(a["reviewers"], b["reviewers"])
        self.assertEqual(a["allocation_basis"], "primary_group_bias_fallback")

    def test_unknown_risk_fails_closed(self):
        with self.assertRaises(ValueError):
            allocate_reviewers("R009", "R9")


if __name__ == "__main__":
    unittest.main()
