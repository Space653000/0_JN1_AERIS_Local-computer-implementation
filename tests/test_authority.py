import unittest

from aeris_runtime.authority import decision


class AuthorityTests(unittest.TestCase):
    def test_r0_is_automatic(self):
        result = decision("R0")
        self.assertTrue(result["automatic_execution_allowed"])
        self.assertTrue(result["execution_allowed"])

    def test_r2_requires_preconditions_and_independent_review(self):
        blocked = decision("R2")
        self.assertFalse(blocked["execution_allowed"])
        self.assertIn("PRECONDITIONS_REQUIRED", blocked["blockers"])
        self.assertIn("INDEPENDENT_REVIEW_REQUIRED", blocked["blockers"])
        allowed = decision("R2", preconditions_passed=True, independent_review_passed=True)
        self.assertTrue(allowed["execution_allowed"])
        self.assertTrue(allowed["automatic_execution_allowed"])

    def test_r3_and_r4_never_self_authorize(self):
        for risk in ["R3", "R4"]:
            result = decision(
                risk,
                independent_review_passed=True,
                human_approved=True,
                human_authority="Human Chief Engineer",
                evidence_refs=["approval://human"],
            )
            self.assertTrue(result["execution_allowed"])
            self.assertFalse(result["automatic_execution_allowed"])

    def test_r4_missing_human_evidence_is_blocked(self):
        result = decision("R4", independent_review_passed=True, human_approved=True, human_authority="Human Chief Engineer")
        self.assertFalse(result["execution_allowed"])
        self.assertIn("APPROVAL_EVIDENCE_REFERENCE_REQUIRED", result["blockers"])


if __name__ == "__main__":
    unittest.main()
