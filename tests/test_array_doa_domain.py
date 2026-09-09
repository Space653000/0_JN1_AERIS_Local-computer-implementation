"""Explicit sample-lag and geometry oracles for a bounded linear pair."""
import unittest
from aeris_runtime.engineering import array_doa
from aeris_runtime.engineering import array_doa_review
from aeris_runtime.engineering import role_acceptance,domain_review
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


def impulse(index):
    return [1.0 if i==index else 0.0 for i in range(256)]


BASE={'channel_1':impulse(100),'channel_2':impulse(101),'sample_rate_hz':16000,
      'band_low_hz':100,'band_high_hz':4000,'spacing_m':0.04,'spacing_lower_m':0.039,'spacing_upper_m':0.041,
      'sound_speed_m_s':343,'sound_speed_lower_m_s':341,'sound_speed_upper_m_s':345,
      'timing_bound_samples':0.5,'estimator_error_bound_samples':0.25,
      'minimum_active_bins':8,'minimum_peak_ratio':1.3,'support_fraction':0.9,
      'peak_exclusion_samples':4,'maximum_support_width_samples':3,
      'array_model':'SYNCHRONIZED_LINEAR_PAIR_FAR_FIELD','channel_polarity':'SAME_POLARITY'}


class ArrayDoaDomainTests(unittest.TestCase):
    def test_alias_and_direction_boundaries_agree_without_clipping_real_excess(self):
        alias={**BASE,'band_high_hz':2561.3984716092446,
               **{k:0.06877070170915545 for k in ('spacing_m','spacing_lower_m','spacing_upper_m')},
               **{k:352.298340498652 for k in ('sound_speed_m_s','sound_speed_lower_m_s','sound_speed_upper_m_s')}}
        output=array_doa.analyze(alias)
        self.assertTrue(output['checks'][2]['passed'])
        self.assertEqual(array_doa_review.review(alias,{**output,'physical_measurement_verified':False})['decision'],'BOUNDED_REVIEW_ACCEPT')
        boundary={**BASE,**{k:343*1.75/16000 for k in ('spacing_m','spacing_lower_m','spacing_upper_m')},
                  **{k:343 for k in ('sound_speed_m_s','sound_speed_lower_m_s','sound_speed_upper_m_s')}}
        result=array_doa.analyze(boundary)
        self.assertTrue(result['checks'][3]['passed'])
        self.assertEqual(array_doa_review.review(boundary,{**result,'physical_measurement_verified':False})['decision'],'BOUNDED_REVIEW_ACCEPT')
        excess={**boundary,**{k:boundary[k]*(1-1e-6) for k in ('spacing_m','spacing_lower_m','spacing_upper_m')}}
        result=array_doa.analyze(excess)
        self.assertFalse(result['checks'][3]['passed'])
        self.assertIsNone(result['planar_angle_interval_deg'])
        self.assertEqual(array_doa_review.review(excess,{**result,'physical_measurement_verified':False})['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_peak_ratio_boundary_agrees_across_independent_fft_paths(self):
        ratio=array_doa.analyze(BASE)['peak_ratio']
        parameters={**BASE,'minimum_peak_ratio':ratio}
        output=array_doa.analyze(parameters)
        self.assertTrue(output['peak_qualified'])
        self.assertEqual(array_doa_review.review(parameters,{**output,'physical_measurement_verified':False})['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_role_suites_and_actual_array_workflow_preserve_bounded_ambiguity(self):
        with isolated_engineering_state():
            runner=role_acceptance.RoleAcceptanceFactory()
            for role in ('R043','R040'):
                result=runner.evaluate(role)
                self.assertTrue(result['execution_passed'],result)
            report=run_role('R043','microphone-array-tdoa-baseline',BASE,
                            objective='Supplied pair lag with geometry uncertainty',source_kind='SYNTHETIC')
            self.assertEqual(report['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual([r['role_id'] for r in report['pod']['reviewers']],['R040'])
            self.assertTrue(domain_review.review_status(report['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(report['evidence_run_id'])['result'],'PASS')

    def test_independent_fft_review_challenges_wrong_sign_scope_and_experiment(self):
        candidate={**array_doa.analyze(BASE),'physical_measurement_verified':False}
        self.assertEqual(array_doa_review.review(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        for field,value in (('delay_samples',-1),('unique_3d_direction_verified',True),
                           ('direction_cosine_interval',[0.5,0.5]),('next_discriminating_experiment','DEPLOY_VERIFIED_ARRAY')):
            with self.subTest(field=field):
                self.assertEqual(array_doa_review.review(BASE,{**candidate,field:value})['decision'],'CHANGES_REQUIRED')

    def test_known_lag_sign_and_interval_never_resolve_unique_3d_direction(self):
        result=array_doa.analyze(BASE)
        self.assertEqual(result['delay_samples'],1)
        self.assertAlmostEqual(result['tdoa_s'],1/16000)
        self.assertAlmostEqual(result['direction_cosine'],343/(16000*0.04))
        self.assertFalse(result['unique_3d_direction_verified'])
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT')
        reversed_result=array_doa.analyze({**BASE,'channel_1':BASE['channel_2'],'channel_2':BASE['channel_1']})
        self.assertEqual(reversed_result['delay_samples'],-1)

    def test_out_of_aperture_dominant_peak_is_not_replaced_with_a_plausible_lag(self):
        result=array_doa.analyze({**BASE,'channel_2':impulse(120)})
        self.assertEqual(result['delay_samples'],20)
        self.assertIsNone(result['planar_angle_interval_deg'])
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_competing_arrivals_and_inverted_polarity_remain_unresolved(self):
        mixed=[a+b for a,b in zip(impulse(92),impulse(108))]
        ambiguous=array_doa.analyze({**BASE,'channel_2':mixed})
        self.assertFalse(ambiguous['peak_qualified'])
        inverted=array_doa.analyze({**BASE,'channel_2':[-x for x in BASE['channel_2']]})
        self.assertFalse(inverted['polarity_consistent'])
        self.assertEqual(inverted['disposition'],'DESIGN_REVISION_REQUIRED')
        symmetric={**BASE,'channel_1':[float(i==127) for i in range(255)],
                   'channel_2':[float(i in (119,135)) for i in range(255)]}
        tied=array_doa.analyze(symmetric)
        self.assertGreaterEqual(tied['peak_tie_count'],2)
        self.assertFalse(tied['peak_qualified'])
        self.assertEqual(array_doa_review.review(symmetric,{**tied,'physical_measurement_verified':False})['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_single_broad_peak_aliasing_and_delay_bounds_do_not_get_confident_angles(self):
        broad=array_doa.analyze({**BASE,'band_low_hz':200,'band_high_hz':600})
        self.assertGreater(broad['peak_support_lags'][1]-broad['peak_support_lags'][0]+1,3)
        self.assertFalse(broad['peak_qualified'])
        self.assertIsNone(broad['planar_angle_interval_deg'])
        for patch in ({'spacing_upper_m':0.06},{'estimator_error_bound_samples':3}):
            result=array_doa.analyze({**BASE,**patch})
            self.assertIsNone(result['planar_angle_interval_deg'])
            self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_unsupported_excitation_and_reference_models_are_rejected(self):
        for change in ({'channel_1':[0.0]*256},{'channel_2':[1.0]*256},{'channel_polarity':'UNKNOWN'},
                       {'spacing_lower_m':0},{'timing_bound_samples':0},
                       {'band_high_hz':8000},{'minimum_active_bins':True},
                       {'channel_2':[1.0]*128},{'array_model':'NEAR_FIELD'}):
            with self.subTest(change=change), self.assertRaises(ValueError): array_doa.analyze({**BASE,**change})


if __name__=='__main__': unittest.main()
