import copy
import unittest

from aeris_runtime import reproduction
from aeris_runtime.engineering import domain_review,hearing_aid_product,hearing_aid_product_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_HEARING_AID_ACOUSTIC_BUDGET","fitting_context":"COUPLER_BASELINE","clinical_fitting_claimed":False,"real_ear_verified":False,"prescribed_insertion_gain_db":20.0,"coupler_gain_db":24.0,"vent_leak_loss_db":2.0,"gain_tolerance_db":1.0,"minimum_gain_margin_db":1.0,"feedback_onset_gain_db":30.0,"minimum_feedback_margin_db":6.0,"input_spl_db":70.0,"maximum_power_output_spl_db":108.0,"maximum_allowed_output_spl_db":110.0,"receiver_output_limit_spl_db":105.0,"minimum_receiver_headroom_db":10.0}


class HearingAidProductTests(unittest.TestCase):
    def test_gain_feedback_mpo_and_headroom_remain_distinct(self):
        result=hearing_aid_product.analyze(BASE)
        self.assertEqual((result['effective_coupler_gain_db'],result['feedback_margin_db'],result['receiver_headroom_db']),(22.0,6.0,13.0))
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT');self.assertFalse(result['clinical_efficacy_verified'])

    def test_vent_and_clinical_claims_fail_closed(self):
        result=hearing_aid_product.analyze({**BASE,'vent_leak_loss_db':4.0})
        self.assertFalse(result['checks'][0]['passed']);self.assertTrue(result['checks'][4]['passed'])
        with self.assertRaises(ValueError): hearing_aid_product.analyze({**BASE,'clinical_fitting_claimed':True})

    def test_independent_review_rejects_medical_overclaim(self):
        candidate=hearing_aid_product.analyze(BASE)
        self.assertEqual(hearing_aid_product_review.review(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        wrong=copy.deepcopy(candidate);wrong['clinical_efficacy_verified']=True
        self.assertEqual(hearing_aid_product_review.review(BASE,wrong)['decision'],'CHANGES_REQUIRED')

    def test_r045_routes_to_exact_r069_acoustic_reviewer(self):
        with isolated_engineering_state():
            runner=role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(runner.evaluate('R045','hearing-aid-gain-feedback-output-baseline')['execution_passed'])
            self.assertTrue(runner.evaluate('R069','hearing-aid-acoustic-boundary-domain-review')['execution_passed'])
            result=run_role('R045','hearing-aid-gain-feedback-output-baseline',BASE,objective='Bound hearing-aid acoustic gain and output',source_kind='SYNTHETIC')
            self.assertEqual(result['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual([row['role_id'] for row in result['pod']['reviewers']],['R069'])
            self.assertTrue(domain_review.review_status(result['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(result['evidence_run_id'])['result'],'PASS')


if __name__=='__main__': unittest.main()
