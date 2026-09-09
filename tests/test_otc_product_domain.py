import copy
import unittest

from aeris_runtime import reproduction
from aeris_runtime.engineering import domain_review,hearing_aid_product,hearing_aid_product_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_OTC_SELF_FIT_OUTPUT_BUDGET","self_fit_mode":"GUIDED_APP","clinical_indication_claimed":False,"physical_user_study_verified":False,"user_gain_setting_db":18.0,"maximum_user_gain_db":20.0,"vent_loss_db":2.0,"self_fit_target_gain_db":16.0,"maximum_target_error_db":2.0,"input_spl_db":75.0,"output_limiter_spl_db":105.0,"maximum_allowed_output_spl_db":110.0,"instruction_comprehension_fraction":0.9,"minimum_instruction_comprehension_fraction":0.8,"seal_repeatability_spread_db":2.0,"maximum_seal_spread_db":3.0}


class OTCProductTests(unittest.TestCase):
    def test_self_fit_output_and_accessibility_plan_are_distinct(self):
        result=hearing_aid_product.analyze_otc(BASE)
        self.assertEqual((result['effective_self_fit_gain_db'],result['predicted_output_spl_db']),(16.0,91.0))
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT');self.assertFalse(result['usability_verified'])
    def test_instruction_and_clinical_claims_fail_closed(self):
        self.assertFalse(hearing_aid_product.analyze_otc({**BASE,'instruction_comprehension_fraction':0.7})['checks'][4]['passed'])
        with self.assertRaises(ValueError): hearing_aid_product.analyze_otc({**BASE,'clinical_indication_claimed':True})
    def test_independent_review_rejects_usability_overclaim(self):
        candidate=hearing_aid_product.analyze_otc(BASE);self.assertEqual(hearing_aid_product_review.review_otc(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        wrong=copy.deepcopy(candidate);wrong['usability_verified']=True;self.assertEqual(hearing_aid_product_review.review_otc(BASE,wrong)['decision'],'CHANGES_REQUIRED')
    def test_r046_routes_to_exact_r070_claims_reviewer(self):
        with isolated_engineering_state():
            runner=role_acceptance.RoleAcceptanceFactory();self.assertTrue(runner.evaluate('R046','otc-self-fit-output-baseline')['execution_passed']);self.assertTrue(runner.evaluate('R070','otc-self-fit-output-claims-domain-review')['execution_passed'])
            result=run_role('R046','otc-self-fit-output-baseline',BASE,objective='Bound OTC self-fit output and instructions',source_kind='SYNTHETIC')
            self.assertEqual(result['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([r['role_id'] for r in result['pod']['reviewers']],['R070'])
            self.assertTrue(domain_review.review_status(result['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(result['evidence_run_id'])['result'],'PASS')


if __name__=='__main__':unittest.main()
