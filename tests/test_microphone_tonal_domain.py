import copy,unittest
from aeris_runtime.engineering import microphone_tonal,microphone_tonal_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state

BASE={'model':'SUPPLIED_MICROPHONE_TONAL_RESPONSE','frequency_hz':[100.0,500.0,1000.0,4000.0,8000.0],'response_db':[-3.0,-1.0,0.0,1.0,-2.0],'target_db':[0.0,0.0,0.0,0.0,0.0],'response_uncertainty_db':0.5,'maximum_boost_db':4.0,'maximum_cut_db':3.0,'input_peak_dbfs':-10.0,'minimum_output_headroom_db':6.0,'highpass_corner_hz':80.0,'maximum_voice_highpass_corner_hz':100.0,'smoothing_fraction_octave':1/6,'maximum_smoothing_fraction_octave':1/3,'capsule_overload_margin_db':8.0,'minimum_capsule_overload_margin_db':6.0}

class MicrophoneTonalTests(unittest.TestCase):
    def test_tonal_voice_and_headroom_bounds(self):
        r=microphone_tonal.analyze(BASE);self.assertEqual(r['proposed_correction_db'],[3.0,1.0,0.0,-1.0,2.0]);self.assertEqual(r['output_headroom_lower_db'],6.5);self.assertFalse(r['intelligibility_verified'])
    def test_highpass_and_frequency_contract_fail_closed(self):
        r=microphone_tonal.analyze({**BASE,'highpass_corner_hz':150.0});self.assertFalse({x['id']:x for x in r['checks']}['VOICE_HIGHPASS']['passed'])
        with self.assertRaises(ValueError):microphone_tonal.analyze({**BASE,'frequency_hz':[100.0,500.0,500.0,4000.0,8000.0]})
    def test_review_rejects_intelligibility_claim(self):
        c=microphone_tonal.analyze(BASE);self.assertEqual(microphone_tonal_review.review(BASE,c)['decision'],'BOUNDED_REVIEW_ACCEPT');wrong=copy.deepcopy(c);wrong['intelligibility_verified']=True;r=microphone_tonal_review.review(BASE,wrong);self.assertEqual(r['decision'],'CHANGES_REQUIRED');self.assertEqual(r['disagreements'][0]['field'],'intelligibility_verified')
    def test_r036_routes_to_r038(self):
        with isolated_engineering_state():
            f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R036','microphone-tonal-headroom-baseline')['execution_passed']);self.assertTrue(f.evaluate('R038','microphone-tonal-intelligibility-domain-review')['execution_passed']);r=run_role('R036','microphone-tonal-headroom-baseline',BASE,objective='Bound microphone tonal headroom and voice corner',source_kind='SYNTHETIC');self.assertEqual(r['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R038']);self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
