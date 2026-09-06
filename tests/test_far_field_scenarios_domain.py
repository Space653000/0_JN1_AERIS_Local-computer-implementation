import copy
import unittest
from aeris_runtime.engineering import far_field_scenarios,far_field_scenarios_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state

SCENARIOS=[{'id':'QUIET-1M','distance_m':1.0,'reference_distance_m':1.0,'speech_reference_rms_pa':0.1,'ambient_noise_rms_pa':0.01,'competing_speech_rms_pa':0.000001,'rt60_s':0.3,'noise_kind':'STATIONARY'},{'id':'FAN-3M','distance_m':3.0,'reference_distance_m':1.0,'speech_reference_rms_pa':0.1,'ambient_noise_rms_pa':0.01,'competing_speech_rms_pa':0.000001,'rt60_s':0.6,'noise_kind':'NONSTATIONARY'},{'id':'TALKER-2M','distance_m':2.0,'reference_distance_m':1.0,'speech_reference_rms_pa':0.1,'ambient_noise_rms_pa':0.005,'competing_speech_rms_pa':0.01,'rt60_s':0.9,'noise_kind':'COMPETING_SPEECH'}]
BASE={'model':'SUPPLIED_FAR_FIELD_SCENARIOS','scenarios':SCENARIOS,'minimum_scenario_count':3,'minimum_maximum_distance_m':3.0,'minimum_worst_case_snr_db':10.0,'maximum_rt60_s':1.0,'require_competing_speech':True}

class FarFieldScenariosTests(unittest.TestCase):
    def test_diverse_scenarios_and_worst_snr(self):
        r=far_field_scenarios.analyze(BASE);self.assertAlmostEqual(r['worst_case_snr_db'],10.457574862177301)
        self.assertTrue(r['competing_speech_covered']);self.assertTrue(r['nonstationary_noise_covered']);self.assertFalse(r['speech_quality_verified'])
    def test_missing_competing_speech_and_duplicate_id_fail_closed(self):
        scenarios=copy.deepcopy(SCENARIOS);scenarios[2]['noise_kind']='STATIONARY';r=far_field_scenarios.analyze({**BASE,'scenarios':scenarios})
        self.assertFalse({x['id']:x for x in r['checks']}['COMPETING_SPEECH_COVERAGE']['passed'])
        duplicate=copy.deepcopy(SCENARIOS);duplicate[2]['id']='QUIET-1M'
        with self.assertRaises(ValueError):far_field_scenarios.analyze({**BASE,'scenarios':duplicate})
    def test_independent_review_rejects_quality_claim(self):
        c=far_field_scenarios.analyze(BASE);self.assertEqual(far_field_scenarios_review.review(BASE,c)['decision'],'BOUNDED_REVIEW_ACCEPT')
        wrong=copy.deepcopy(c);wrong['speech_quality_verified']=True;r=far_field_scenarios_review.review(BASE,wrong)
        self.assertEqual(r['decision'],'CHANGES_REQUIRED');self.assertEqual(r['disagreements'][0]['field'],'speech_quality_verified')
    def test_r035_routes_to_exact_r041_disturbance_reviewer(self):
        with isolated_engineering_state():
            f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R035','microphone-far-field-scenarios-baseline')['execution_passed']);self.assertTrue(f.evaluate('R041','microphone-far-field-disturbance-domain-review')['execution_passed'])
            r=run_role('R035','microphone-far-field-scenarios-baseline',BASE,objective='Bound far-field distance noise and room scenarios',source_kind='SYNTHETIC')
            self.assertEqual(r['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R041'])
            self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
