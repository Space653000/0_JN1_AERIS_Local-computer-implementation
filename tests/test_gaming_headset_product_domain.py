import copy
import unittest

from aeris_runtime import reproduction
from aeris_runtime.engineering import domain_review,personal_device_products,personal_device_products_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state


BASE={"model":"SUPPLIED_GAMING_HEADSET_COMMUNICATION_BUDGET","microphone_topology":"BOOM_MICROPHONE","physical_call_verified":False,"capture_buffer_ms":2.0,"sidetone_processing_ms":1.0,"playback_buffer_ms":2.0,"maximum_sidetone_latency_ms":10.0,"boom_mic_distance_m":0.05,"minimum_boom_distance_m":0.03,"maximum_boom_distance_m":0.08,"speaker_to_mic_crosstalk_db":-45.0,"maximum_crosstalk_db":-40.0,"voice_snr_db":25.0,"minimum_voice_snr_db":20.0,"output_headroom_db":6.0,"minimum_output_headroom_db":3.0}


class GamingHeadsetProductTests(unittest.TestCase):
    def test_local_latency_and_duplex_budgets_are_distinct(self):
        result=personal_device_products.analyze_gaming(BASE)
        self.assertEqual(result['sidetone_latency_ms'],5.0)
        self.assertEqual([c['id'] for c in result['checks']],['SIDETONE_LATENCY','BOOM_DISTANCE_MINIMUM','BOOM_DISTANCE_MAXIMUM','PLAYBACK_CROSSTALK','VOICE_SNR','OUTPUT_HEADROOM'])
        self.assertFalse(result['communication_quality_verified'])

    def test_boom_and_physical_claims_fail_closed(self):
        self.assertFalse(personal_device_products.analyze_gaming({**BASE,'boom_mic_distance_m':0.01})['checks'][1]['passed'])
        with self.assertRaises(ValueError):
            personal_device_products.analyze_gaming({**BASE,'physical_call_verified':True})

    def test_reviewer_rejects_communication_overclaim(self):
        candidate=personal_device_products.analyze_gaming(BASE)
        self.assertEqual(personal_device_products_review.review_gaming(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        wrong=copy.deepcopy(candidate);wrong['communication_quality_verified']=True
        self.assertEqual(personal_device_products_review.review_gaming(BASE,wrong)['decision'],'CHANGES_REQUIRED')

    def test_r050_routes_to_exact_r082_reviewer(self):
        with isolated_engineering_state():
            factory=role_acceptance.RoleAcceptanceFactory()
            self.assertTrue(factory.evaluate('R050','gaming-headset-communication-baseline')['execution_passed'])
            self.assertTrue(factory.evaluate('R082','gaming-communication-latency-domain-review')['execution_passed'])
            result=run_role('R050','gaming-headset-communication-baseline',BASE,objective='Bound gaming communication architecture',source_kind='SYNTHETIC')
            self.assertEqual(result['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual([r['role_id'] for r in result['pod']['reviewers']],['R082'])
            self.assertTrue(domain_review.review_status(result['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(result['evidence_run_id'])['result'],'PASS')


if __name__=='__main__':unittest.main()
