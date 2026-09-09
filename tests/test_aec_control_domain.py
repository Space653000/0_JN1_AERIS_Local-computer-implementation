import copy,unittest
from aeris_runtime.engineering import aec_control,aec_control_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state

BASE={'model':'SUPPLIED_ECHO_CONTROL_METRICS','echo_return_before_rms':0.05,'echo_residual_after_rms':0.005,'minimum_erle_db':15.0,'near_speech_before_rms':0.03,'near_speech_after_rms':0.028,'maximum_near_speech_loss_db':1.0,'alignment_delay_ms':50.0,'maximum_alignment_delay_ms':80.0,'clock_drift_ppm':10.0,'maximum_clock_drift_ppm':20.0,'double_talk_adaptation_gain':0.05,'maximum_double_talk_adaptation_gain':0.1,'adaptive_filter_tail_ms':150.0,'minimum_required_echo_tail_ms':120.0,'nonlinear_residual_rms':0.002,'maximum_nonlinear_residual_rms':0.003}

class AecControlTests(unittest.TestCase):
    def test_alignment_double_talk_and_tail_bounds(self):
        r=aec_control.analyze(BASE);self.assertEqual(r['erle_db'],20.0);self.assertAlmostEqual(r['near_speech_loss_db'],0.5992644675488641);self.assertEqual(r['echo_tail_margin_ms'],30.0);self.assertFalse(r['speech_quality_verified'])
    def test_double_talk_and_impossible_residual_fail_closed(self):
        r=aec_control.analyze({**BASE,'double_talk_adaptation_gain':0.2});self.assertFalse({x['id']:x for x in r['checks']}['DOUBLE_TALK_ADAPTATION']['passed'])
        with self.assertRaises(ValueError):aec_control.analyze({**BASE,'echo_residual_after_rms':0.06})
    def test_review_rejects_quality_claim(self):
        c=aec_control.analyze(BASE);self.assertEqual(aec_control_review.review(BASE,c)['decision'],'BOUNDED_REVIEW_ACCEPT');wrong=copy.deepcopy(c);wrong['speech_quality_verified']=True;r=aec_control_review.review(BASE,wrong);self.assertEqual(r['decision'],'CHANGES_REQUIRED');self.assertEqual(r['disagreements'][0]['field'],'speech_quality_verified')
    def test_r042_routes_to_r044(self):
        with isolated_engineering_state():
            f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R042','microphone-aec-control-baseline')['execution_passed']);self.assertTrue(f.evaluate('R044','microphone-aec-enhancement-domain-review')['execution_passed']);r=run_role('R042','microphone-aec-control-baseline',BASE,objective='Bound echo alignment drift double-talk and tail',source_kind='SYNTHETIC');self.assertEqual(r['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R044']);self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
