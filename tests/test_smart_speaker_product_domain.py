import copy
import unittest
from aeris_runtime import reproduction
from aeris_runtime.engineering import conference_products,conference_products_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_SMART_SPEAKER_FAR_FIELD_SELF_ECHO_BUDGET","array_topology":"CIRCULAR_ARRAY_DECLARED","physical_smart_speaker_verified":False,"woofer_to_mic_coupling_db":-45.0,"maximum_woofer_to_mic_coupling_db":-40.0,"wakeword_snr_db":15.0,"minimum_wakeword_snr_db":10.0,"array_aliasing_frequency_hz":8000.0,"minimum_array_aliasing_frequency_hz":6000.0,"talker_azimuth_count":8,"minimum_talker_azimuth_count":6,"room_mode_spread_db":4.0,"maximum_room_mode_spread_db":6.0,"aec_tail_ms":300.0,"minimum_aec_tail_ms":250.0}

class SmartSpeakerProductTests(unittest.TestCase):
    def test_self_echo_array_and_room_are_distinct(self):
        r=conference_products.analyze_smart_speaker(BASE);self.assertEqual([c['id'] for c in r['checks']],['WOOFER_MIC_COUPLING','WAKEWORD_SNR','ARRAY_ALIASING_FREQUENCY','TALKER_AZIMUTH_COVERAGE','ROOM_MODE_SPREAD','AEC_TAIL_COVERAGE']);self.assertFalse(r['wakeword_quality_verified'])
    def test_coupling_and_physical_claim_fail_closed(self):
        self.assertFalse(conference_products.analyze_smart_speaker({**BASE,'woofer_to_mic_coupling_db':-35.0})['checks'][0]['passed'])
        with self.assertRaises(ValueError):conference_products.analyze_smart_speaker({**BASE,'physical_smart_speaker_verified':True})
    def test_reviewer_rejects_wakeword_overclaim(self):
        c=conference_products.analyze_smart_speaker(BASE);self.assertEqual(conference_products_review.review_smart_speaker(BASE,c)['decision'],'BOUNDED_REVIEW_ACCEPT');w=copy.deepcopy(c);w['wakeword_quality_verified']=True;self.assertEqual(conference_products_review.review_smart_speaker(BASE,w)['decision'],'CHANGES_REQUIRED')
    def test_r055_routes_to_r035(self):
        with isolated_engineering_state():
            f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R055','smart-speaker-far-field-self-echo-baseline')['execution_passed']);self.assertTrue(f.evaluate('R035','smart-speaker-far-field-self-echo-domain-review')['execution_passed']);r=run_role('R055','smart-speaker-far-field-self-echo-baseline',BASE,objective='Bound smart-speaker architecture',source_kind='SYNTHETIC');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R035']);self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
