import copy
import unittest

from aeris_runtime import reproduction
from aeris_runtime.engineering import domain_review,personal_device_products,personal_device_products_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state


BASE={"model":"SUPPLIED_SMARTPHONE_HAND_BLOCK_MESH_ECHO_BUDGET","port_protection":"WATER_MESH_DECLARED","physical_handset_verified":False,"hand_blockage_loss_db":2.0,"maximum_hand_blockage_loss_db":3.0,"water_mesh_loss_db":1.5,"maximum_water_mesh_loss_db":2.0,"speaker_to_mic_echo_coupling_db":-45.0,"maximum_echo_coupling_db":-40.0,"orientation_count":6,"minimum_orientation_count":4,"bottom_speaker_peak_excursion_mm":0.3,"safe_bottom_speaker_excursion_mm":0.5,"handheld_call_snr_db":22.0,"minimum_handheld_call_snr_db":20.0}


class SmartphoneProductTests(unittest.TestCase):
    def test_hand_mesh_echo_and_excursion_are_distinct(self):
        result=personal_device_products.analyze_smartphone(BASE)
        self.assertEqual([c['id'] for c in result['checks']],['HAND_BLOCKAGE','WATER_MESH_LOSS','ECHO_COUPLING','ORIENTATION_COVERAGE','BOTTOM_SPEAKER_EXCURSION','HANDHELD_CALL_SNR'])
        self.assertFalse(result['mesh_transfer_verified'])
        self.assertFalse(result['aec_verified'])

    def test_hand_block_and_physical_claims_fail_closed(self):
        self.assertFalse(personal_device_products.analyze_smartphone({**BASE,'hand_blockage_loss_db':4.0})['checks'][0]['passed'])
        with self.assertRaises(ValueError):
            personal_device_products.analyze_smartphone({**BASE,'physical_handset_verified':True})

    def test_reviewer_rejects_mesh_overclaim(self):
        candidate=personal_device_products.analyze_smartphone(BASE)
        self.assertEqual(personal_device_products_review.review_smartphone(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        wrong=copy.deepcopy(candidate);wrong['mesh_transfer_verified']=True
        self.assertEqual(personal_device_products_review.review_smartphone(BASE,wrong)['decision'],'CHANGES_REQUIRED')

    def test_r051_routes_to_exact_r077_reviewer(self):
        with isolated_engineering_state():
            factory=role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(factory.evaluate('R051','smartphone-port-mesh-echo-baseline')['execution_passed'])
            self.assertTrue(factory.evaluate('R077','smartphone-port-mesh-echo-domain-review')['execution_passed'])
            result=run_role('R051','smartphone-port-mesh-echo-baseline',BASE,objective='Bound smartphone port and echo architecture',source_kind='SYNTHETIC')
            self.assertEqual(result['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual([r['role_id'] for r in result['pod']['reviewers']],['R077'])
            self.assertTrue(domain_review.review_status(result['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(result['evidence_run_id'])['result'],'PASS')


if __name__=='__main__':unittest.main()
