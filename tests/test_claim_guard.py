import json
import unittest

from aeris_runtime.claim_guard import render_guarded_output, validate_role_output
from aeris_runtime.roles import get_role, system_prompt


class ClaimGuardTests(unittest.TestCase):
    def test_plain_model_prose_is_rejected_instead_of_rendered_as_engineering_truth(self):
        guarded = validate_role_output("我們已經有量測記錄，頻響符合規格。")
        self.assertFalse(guarded["accepted"])
        rendered = render_guarded_output(guarded)
        self.assertIn("Evidence Guard", rendered)
        self.assertNotIn("頻響符合規格", rendered)

    def test_evidence_claim_without_authoritative_ref_is_rejected(self):
        raw = json.dumps({
            "claims": [{
                "statement": "量測結果顯示 1 kHz 為 92 dB SPL",
                "classification": "EVIDENCE",
                "evidence_refs": [],
                "confidence": 0.99,
            }],
            "missing_evidence": [],
            "recommended_tests": [],
        }, ensure_ascii=False)
        guarded = validate_role_output(raw)
        self.assertFalse(guarded["accepted"])
        self.assertTrue(any("requires approved evidence_refs" in x for x in guarded["errors"]))

    def test_measured_fact_wording_cannot_hide_under_inference(self):
        raw = json.dumps({
            "claims": [{
                "statement": "已有量測記錄證明此單體通過測試",
                "classification": "INFERENCE",
                "evidence_refs": [],
                "confidence": 0.8,
            }],
            "missing_evidence": [],
            "recommended_tests": [],
        }, ensure_ascii=False)
        guarded = validate_role_output(raw)
        self.assertFalse(guarded["accepted"])
        self.assertTrue(any("measured/verified-fact wording" in x for x in guarded["errors"]))

    def test_inference_without_fabricated_measurement_is_allowed(self):
        raw = json.dumps({
            "claims": [{
                "statement": "依目前幾何條件推測，箱體共振可能影響 200 Hz 附近響應",
                "classification": "HYPOTHESIS",
                "evidence_refs": [],
                "confidence": 0.55,
            }],
            "missing_evidence": ["需要取得實際頻率響應資料"],
            "recommended_tests": ["執行近場與遠場頻率響應量測"],
        }, ensure_ascii=False)
        guarded = validate_role_output(raw)
        self.assertTrue(guarded["accepted"])
        self.assertEqual(guarded["claim_authority"], "SCHEMA_VALIDATED_INFERENCE_ONLY")

    def test_evidence_claim_with_explicit_approved_ref_is_allowed(self):
        ref = ".aeris/evidence/RUN-123/manifest.json"
        raw = json.dumps({
            "claims": [{
                "statement": "量測結果顯示 1 kHz 為 92 dB SPL",
                "classification": "EVIDENCE",
                "evidence_refs": [ref],
                "confidence": 1.0,
            }],
            "missing_evidence": [],
            "recommended_tests": [],
        }, ensure_ascii=False)
        guarded = validate_role_output(raw, approved_evidence_refs=[ref])
        self.assertTrue(guarded["accepted"])
        self.assertEqual(guarded["claim_authority"], "SCHEMA_VALIDATED_WITH_EXPLICIT_EVIDENCE_REFS")

    def test_role_prompt_forbids_evidence_when_none_supplied(self):
        prompt = system_prompt(get_role("R001"), [])
        self.assertIn("Return ONLY one JSON object", prompt)
        self.assertIn("NO claim may be classified EVIDENCE", prompt)
        self.assertIn("Knowledge snippets are retrieval context, NOT engineering Evidence", prompt)


if __name__ == "__main__":
    unittest.main()
