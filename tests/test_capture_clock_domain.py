"""Capture continuity is distinct from callback latency and acoustic TDOA."""
import copy
import random
import unittest
from aeris_runtime.engineering.capture_clock import analyze
from aeris_runtime.engineering.capture_clock_review import review
from aeris_runtime.engineering import domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    'model':'FIRST_SAMPLE_CAPTURE_TIMESTAMP_V1',
    'reference_rate_assumption':'UNVERIFIED_REFERENCE_TIMESCALE',
    'capture_clock_id':'reference-A', 'delivery_clock_id':'reference-A',
    'timestamp_kind':'FIRST_SAMPLE_ACQUISITION',
    'clock_mode':'PDM_INTEGER_DECIMATION', 'pdm_clock_hz':3072000, 'decimation_ratio':64,
    'sample_rate_hz':48000, 'frame_samples':480,
    'sample_width_bits':24, 'slot_width_bits':32,
    'expected_channel_ids':['left','right'], 'observed_slot_order':['left','right'],
    'timestamp_resolution_ns':1, 'allowed_rate_error_ppm':50,
    'allowed_alignment_skew_samples':0.1, 'maximum_delivery_latency_ms':5,
    'maximum_nominal_rate_timing_residual_ns':1000,
    'channels':[{'channel_id':channel,'frames':[
        {'frame_seq':i, 'first_sample_index':i*480, 'sample_count':480,
         'capture_timestamp_ns':i*10000000, 'delivery_timestamp_ns':i*10000000+1000000}
        for i in range(3)]} for channel in ('left','right')],
}


class CaptureClockTests(unittest.TestCase):
    def test_long_observation_preserves_nonzero_bounds_and_reviewer_rejects_zeroing(self):
        p=copy.deepcopy(BASE);p['allowed_rate_error_ppm']=0
        for c in p['channels']:
            c['frames']=c['frames'][:2]
            c['frames'][1].update(first_sample_index=192000000000,
                capture_timestamp_ns=4000000000000000,delivery_timestamp_ns=4000000001000000)
        result=analyze(p);bounds=result['channels'][0]['relative_rate_interval_ppm']
        self.assertLess(bounds[0],0)
        self.assertGreater(bounds[1],0)
        self.assertEqual(result['checks'][1]['state'],'INCONCLUSIVE')
        lie=copy.deepcopy(result);lie['channels'][0]['relative_rate_interval_ppm']=[0,0]
        self.assertEqual(review(p,lie)['decision'],'CHANGES_REQUIRED')

    def test_large_counter_delta_requires_exact_review_not_relative_float_tolerance(self):
        p=copy.deepcopy(BASE)
        for c in p['channels']:
            for i,f in enumerate(c['frames']):f['first_sample_index']=i*10**12
        result=analyze(p)
        self.assertEqual(review(p,result)['decision'],'BOUNDED_REVIEW_ACCEPT')
        lie=copy.deepcopy(result);lie['channels'][0]['continuity_issues'][0]['delta']+=100
        self.assertEqual(review(p,lie)['decision'],'CHANGES_REQUIRED')

    def test_independent_integer_clock_reconstruction_across_reference_offsets(self):
        rng=random.Random(31032)
        for _ in range(24):
            p=copy.deepcopy(BASE)
            p['timestamp_resolution_ns']=rng.choice([1,10,100,1000,100000000])
            period=10000000+rng.randint(-10000,10000)
            offset=rng.randint(0,50000)
            for n,c in enumerate(p['channels']):
                for i,f in enumerate(c['frames']):
                    f['capture_timestamp_ns']=i*period+n*offset
                    f['delivery_timestamp_ns']=f['capture_timestamp_ns']+rng.randint(1,6000000)
            result=analyze(p)
            self.assertEqual(review(p,result)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_role_evidence_routes_to_clock_reviewer_and_reproduces_without_upgrading_l3(self):
        with isolated_engineering_state():
            request={'product':'R068','transducer':'Microphone','lifecycle':'EVT','risk':'R1',
                'source_kind':'SYNTHETIC','needed_skills':['microphone-capture-continuity-baseline'],
                'required_evidence':['sealed numerical run','independent counterreview']}
            self.assertFalse(domain_review.select_reviewers(request,['R032'])['complete'])
            runner=role_acceptance.RoleAcceptanceFactory()
            for role,count in (('R031',14),('R032',17)):
                status=runner.evaluate(role)
                self.assertTrue(status['execution_passed'],status)
                self.assertEqual(status['case_count'],count)
                self.assertEqual(status['level'],'L2')
                self.assertFalse(status['role_l3_accepted'])
            self.assertTrue(domain_review.select_reviewers(request,['R032'])['complete'])
            self.assertFalse(domain_review.select_reviewers({**request,'conflicted_role_ids':['R031']},['R032'])['complete'])
            accepted=run_role('R032','microphone-capture-continuity-baseline',BASE,
                objective='Separate sample counter continuity from relative clock accuracy',source_kind='SYNTHETIC')
            self.assertEqual(accepted['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual([r['role_id'] for r in accepted['pod']['reviewers']],['R031'])
            self.assertTrue(domain_review.review_status(accepted['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(accepted['evidence_run_id'])['result'],'PASS')
            rejected=run_role('R032','microphone-capture-continuity-baseline',{**BASE,'maximum_delivery_latency_ms':1},
                objective='Preserve uncertainty-crossing delivery interval as unresolved',source_kind='SYNTHETIC')
            self.assertEqual(rejected['review']['decision'],'DESIGN_REVISION_REQUIRED')

    def test_independent_review_rejects_nominal_only_bounds_and_false_physical_claims(self):
        p=copy.deepcopy(BASE);p.update(timestamp_resolution_ns=100,maximum_nominal_rate_timing_residual_ns=100)
        for c in p['channels']:c['frames'][1]['capture_timestamp_ns']+=150
        result=analyze(p)
        self.assertEqual(review(p,result)['decision'],'BOUNDED_REVIEW_ACCEPT')
        for field,value in (('absolute_oscillator_accuracy_verified',True),('unresolved',[]),
                            ('limitations',[]),('disposition','BOUNDED_BASELINE_ACCEPT')):
            with self.subTest(field=field):
                self.assertEqual(review(p,{**result,field:value})['decision'],'CHANGES_REQUIRED')
        lie=copy.deepcopy(result);lie['channels'][0]['absolute_timing_residual_intervals_ns'][0]=[150,150]
        self.assertEqual(review(p,lie)['decision'],'CHANGES_REQUIRED')

    def test_nominal_pdm_capture_contract_is_not_absolute_clock_or_physical_acceptance(self):
        r=analyze(BASE)
        self.assertEqual(r['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertEqual(r['channels'][0]['relative_rate_error_ppm'],0)
        for field in ('physical_capture_verified','bitstream_filter_verified',
                      'clock_phase_noise_verified','absolute_oscillator_accuracy_verified','role_l3_accepted'):
            self.assertIs(r[field],False)

    def test_dropped_frame_does_not_fabricate_clock_drift(self):
        p=copy.deepcopy(BASE)
        for channel in p['channels']:
            for i,j in enumerate((0,2,3)):
                channel['frames'][i].update(frame_seq=j,first_sample_index=j*480,
                    capture_timestamp_ns=j*10000000,delivery_timestamp_ns=j*10000000+1000000)
        r=analyze(p)
        self.assertEqual(r['channels'][0]['relative_rate_error_ppm'],0)
        self.assertEqual(r['checks'][0]['state'],'FAIL')
        self.assertEqual(r['checks'][1]['state'],'PASS')

    def test_high_callback_latency_is_not_acquisition_skew(self):
        p=copy.deepcopy(BASE)
        for f in p['channels'][1]['frames']:f['delivery_timestamp_ns']+=10000000
        r=analyze(p)
        self.assertEqual(r['checks'][4]['state'],'FAIL')
        self.assertEqual(r['checks'][3]['state'],'PASS')

    def test_resolution_crossing_timing_limit_is_inconclusive_not_pass(self):
        p=copy.deepcopy(BASE);p.update(timestamp_resolution_ns=100,maximum_nominal_rate_timing_residual_ns=100)
        for c in p['channels']:
            c['frames'][1]['capture_timestamp_ns']+=150
        r=analyze(p)
        self.assertEqual(r['checks'][2]['state'],'INCONCLUSIVE')
        self.assertNotEqual(r['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_callback_or_unrelated_or_claimed_calibrated_clock_is_rejected(self):
        for patch in ({'timestamp_kind':'CALLBACK_ARRIVAL'}, {'delivery_clock_id':'other'},
                      {'reference_rate_assumption':'CALIBRATED'}, {'sample_rate_hz':True},
                      {'absolute_oscillator_accuracy_verified':True}, {'channels':[]}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):analyze({**BASE,**patch})


if __name__=='__main__':unittest.main()
