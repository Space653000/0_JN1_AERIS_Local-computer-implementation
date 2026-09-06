import copy
import unittest

from aeris_runtime import reproduction
from aeris_runtime.engineering import domain_review,personal_device_products,personal_device_products_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_LAPTOP_FAN_HINGE_COUPLING_BUDGET","fan_operating_set":"IDLE_NOMINAL_TURBO","physical_laptop_verified":False,"fan_harmonic_capture_db":-30.0,"maximum_fan_harmonic_capture_db":-25.0,"hinge_angle_count":5,"minimum_hinge_angle_count":3,"array_transfer_spread_db":2.0,"maximum_array_transfer_spread_db":3.0,"keyboard_body_coupling_db":-35.0,"maximum_keyboard_body_coupling_db":-30.0,"speaker_headroom_db":6.0,"minimum_speaker_headroom_db":3.0,"aec_reference_alignment_ms":2.0,"maximum_aec_reference_alignment_ms":5.0}

class LaptopProductTests(unittest.TestCase):
    def test_fan_hinge_and_body_paths_are_distinct(self):
        result=personal_device_products.analyze_laptop(BASE)
        self.assertEqual([c['id'] for c in result['checks']],['FAN_HARMONIC_CAPTURE','HINGE_ANGLE_COVERAGE','ARRAY_TRANSFER_SPREAD','KEYBOARD_BODY_COUPLING','SPEAKER_HEADROOM','AEC_REFERENCE_ALIGNMENT'])
        self.assertFalse(result['fan_path_verified'])
    def test_fan_and_physical_claim_fail_closed(self):
        self.assertFalse(personal_device_products.analyze_laptop({**BASE,'fan_harmonic_capture_db':-20.0})['checks'][0]['passed'])
        with self.assertRaises(ValueError):personal_device_products.analyze_laptop({**BASE,'physical_laptop_verified':True})
    def test_reviewer_rejects_aec_overclaim(self):
        candidate=personal_device_products.analyze_laptop(BASE);self.assertEqual(personal_device_products_review.review_laptop(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        wrong=copy.deepcopy(candidate);wrong['aec_verified']=True
        self.assertEqual(personal_device_products_review.review_laptop(BASE,wrong)['decision'],'CHANGES_REQUIRED')
    def test_r053_routes_to_exact_r073_reviewer(self):
        with isolated_engineering_state():
            factory=role_acceptance.RoleAcceptanceFactory();self.assertTrue(factory.evaluate('R053','laptop-fan-hinge-coupling-baseline')['execution_passed']);self.assertTrue(factory.evaluate('R073','laptop-fan-hinge-coupling-domain-review')['execution_passed'])
            result=run_role('R053','laptop-fan-hinge-coupling-baseline',BASE,objective='Bound laptop fan and hinge architecture',source_kind='SYNTHETIC')
            self.assertEqual(result['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([r['role_id'] for r in result['pod']['reviewers']],['R073']);self.assertTrue(domain_review.review_status(result['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(result['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
