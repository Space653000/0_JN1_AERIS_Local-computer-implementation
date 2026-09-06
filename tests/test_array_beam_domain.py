"""Authored ULA transfer and covariance oracles, independent of implementation."""
import math
import copy
import unittest
from aeris_runtime.engineering import array_beam
from aeris_runtime.engineering import array_beam_review
from aeris_runtime.engineering import role_acceptance,domain_review
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state

BASE={'model':'FAR_FIELD_ULA_TRUE_TIME_DELAY','noise_model':'UNCORRELATED_EQUAL_VARIANCE_BEFORE_GAIN',
      'weights':[1,1],'channel_gains':[1,1],'channel_delays_s':[0,0],
      'gain_bounds':[0,0],'delay_bounds_s':[0,0],'position_bounds_m':[0,0],
      'spacing_m':0.085,'frequencies_hz':[2000],'angles_deg':[-90,-60,-30,0,30,60,90],
      'steering_deg':0,'sound_speed_m_s':340,'source_range_m':10,
      'minimum_range_aperture_ratio':5,'minimum_fraunhofer_ratio':1,
      'main_lobe_exclusion_deg':30,'maximum_grid_gap_deg':30,
      'minimum_desired_amplitude':0.8,'maximum_sampled_sidelobe_amplitude':0.8,'minimum_white_noise_gain':1.5}


class ArrayBeamTests(unittest.TestCase):
    def test_common_taper_scale_cannot_underflow_independent_review(self):
        for scale in (1e-200,5e-324,1e6):
            p={**BASE,'weights':[scale,scale]};value=array_beam.analyze(p)
            with self.subTest(scale=scale):
                self.assertAlmostEqual(value['output_noise_variance_ratio'],0.5)
                self.assertEqual(array_beam_review.review(p,value)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_half_wavelength_pair_has_unity_broadside_null_endfire_and_wng_two(self):
        result=array_beam.analyze(BASE);band=result['bands'][0]
        self.assertAlmostEqual(band['desired_amplitude'],1)
        self.assertAlmostEqual(band['white_noise_gain'],2)
        self.assertAlmostEqual(band['sample_amplitudes'][0],0,places=12)
        self.assertAlmostEqual(band['sample_amplitudes'][2],math.sqrt(0.5))
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_single_active_weight_is_not_a_narrow_robust_array(self):
        result=array_beam.analyze({**BASE,'weights':[1,0]});band=result['bands'][0]
        self.assertAlmostEqual(band['white_noise_gain'],1)
        self.assertEqual(band['sample_amplitudes'],[1]*7)
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_positive_delay_cancels_geometry_at_nonzero_steering(self):
        p={**BASE,'spacing_m':0.05,'frequencies_hz':[1700],'steering_deg':30,
           'channel_delays_s':[0,0.025/340]}
        positive=array_beam.analyze(p)['bands'][0]['sample_amplitudes'][-1]
        negative=array_beam.analyze({**p,'channel_delays_s':[0,-0.025/340]})['bands'][0]['sample_amplitudes'][-1]
        self.assertAlmostEqual(positive,1)
        self.assertAlmostEqual(negative,math.sqrt(0.5))

    def test_supplied_error_bounds_widen_gain_without_fake_measurement(self):
        r=array_beam.analyze({**BASE,'gain_bounds':[0.1,0.1]});b=r['bands'][0]
        self.assertAlmostEqual(b['desired_lower'],0.9)
        self.assertAlmostEqual(b['desired_upper'],1.1)
        self.assertAlmostEqual(b['white_noise_gain_lower'],0.81/0.605)
        self.assertFalse(r['physical_measurement_verified'])
        self.assertFalse(r['continuous_angle_verified'])
        self.assertFalse(r['speech_quality_verified'])

    def test_alias_near_field_sparse_grid_and_desired_null_fail_design(self):
        for patch in ({'spacing_m':0.1},{'source_range_m':0.1},
                      {'angles_deg':[-90,0,90]}, {'channel_delays_s':[0,0.00025]}):
            with self.subTest(patch=patch):
                r=array_beam.analyze({**BASE,**patch})
                self.assertEqual(r['disposition'],'DESIGN_REVISION_REQUIRED')
        r=array_beam.analyze({**BASE,'channel_delays_s':[0,0.00025]})
        self.assertAlmostEqual(r['bands'][0]['white_noise_gain'],0,places=20)

    def test_unsupported_covariance_and_invalid_geometry_fail_closed(self):
        for patch in ({'noise_model':'FULLY_CORRELATED'},{'weights':[0,0]},
                      {'channel_gains':[1]},{'angles_deg':[-90,30,0,90]},
                      {'frequencies_hz':[2000,1000]},{'gain_bounds':[1,0]},
                      {'position_bounds_m':[0.1,0]},{'spacing_mm':85},
                      {'steering_deg':float('nan')},{'channel_delays_s':[False,0]}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                array_beam.analyze({**BASE,**patch})

    def test_independent_report_review_rejects_suppressed_uncertainty_and_false_claims(self):
        p={**BASE,'gain_bounds':[0.1,0.1]};original=array_beam.analyze(p)
        self.assertEqual(array_beam_review.review(p,original)['decision'],'BOUNDED_REVIEW_ACCEPT')
        for key,value in (('physical_measurement_verified',True),('continuous_angle_verified',True),
                          ('speech_quality_verified',True),('unresolved',[]),('counter_hypotheses',[])):
            with self.subTest(key=key):
                self.assertEqual(array_beam_review.review(p,{**original,key:value})['decision'],'CHANGES_REQUIRED')
        lie=copy.deepcopy(original);lie['bands'][0]['desired_lower']=1
        self.assertEqual(array_beam_review.review(p,lie)['decision'],'CHANGES_REQUIRED')
        lie=copy.deepcopy(original);lie['checks'][5]['passed']=True
        self.assertEqual(array_beam_review.review(p,lie)['decision'],'CHANGES_REQUIRED')

    def test_role_suites_execute_real_workflow_with_pattern_specialist_and_reproduction(self):
        with isolated_engineering_state():
            runner=role_acceptance.RoleAcceptanceFactory()
            for role,skill in (
                    ('R037','microphone-array-taper-baseline'),
                    ('R034','microphone-array-pattern-domain-review')):
                result=runner.evaluate(role,skill)
                self.assertTrue(result['execution_passed'],result)
                self.assertEqual(result['case_count'],15)
                self.assertEqual(result['level'],'L2')
                self.assertFalse(result['role_l3_accepted'])
            accepted=run_role('R037','microphone-array-taper-baseline',BASE,
                objective='Evaluate sampled taper with independent array-pattern reviewer',source_kind='SYNTHETIC')
            self.assertEqual(accepted['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual([r['role_id'] for r in accepted['pod']['reviewers']],['R034'])
            self.assertTrue(domain_review.review_status(accepted['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(accepted['evidence_run_id'])['result'],'PASS')
            rejected=run_role('R037','microphone-array-taper-baseline',{**BASE,'gain_bounds':[0.1,0.1]},
                objective='Keep robust WNG failure visible despite nominal gain',source_kind='SYNTHETIC')
            self.assertEqual(rejected['review']['decision'],'DESIGN_REVISION_REQUIRED')


if __name__=='__main__':unittest.main()
