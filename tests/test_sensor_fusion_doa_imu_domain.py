"""Independent worked decisions for the IMU/acoustic-DOA circular fusion
baseline, not L4 or physical bench-verified claims."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'imu_heading_deg':10.0,'imu_heading_std_deg':5.0,'imu_timestamp_s':0.0,
      'acoustic_doa_deg':20.0,'acoustic_doa_std_deg':10.0,'acoustic_timestamp_s':0.005,
      'max_acceptable_timestamp_skew_s':0.05,'max_acceptable_fused_std_deg':10.0}


class SensorFusionDoaImuDomainTests(unittest.TestCase):
    def test_nominal_fusion_matches_independent_worked_calculation(self):
        values=run_skill('sensor-fusion-doa-imu-baseline',BASE)['values']
        self.assertAlmostEqual(values['fused_heading_deg'],11.995119288508716)
        self.assertAlmostEqual(values['fused_heading_std_deg'],4.47213595499958)
        self.assertFalse(values['frame_reversal_suspected'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_fusion_is_correct_across_the_0_360_wrap_boundary(self):
        """A naive linear average of 350 and 10 degrees gives 180 (exactly
        backwards); the true difference is 20 degrees and the circular
        fusion must reflect that, not the wraparound artifact."""
        values=run_skill('sensor-fusion-doa-imu-baseline',
            {**BASE,'imu_heading_deg':350.0,'acoustic_doa_deg':10.0})['values']
        self.assertAlmostEqual(values['circular_disagreement_deg'],-19.999999999999993)
        self.assertAlmostEqual(values['fused_heading_deg'],-6.039209988994377)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_near_180_disagreement_flags_frame_reversal_instead_of_fusing_through_it(self):
        values=run_skill('sensor-fusion-doa-imu-baseline',
            {**BASE,'acoustic_doa_deg':190.0})['values']
        self.assertAlmostEqual(values['circular_disagreement_deg'],180.0)
        self.assertTrue(values['frame_reversal_suspected'])
        self.assertEqual(values['disposition'],'POSSIBLE_FRAME_CONVENTION_REVERSAL')
        self.assertIn('CONFIRM_IMU_AND_ACOUSTIC_HEADING_SHARE_THE_SAME_SIGN_CONVENTION_BEFORE_TRUSTING_THIS_FUSION',
                       values['required_revisions'])

    def test_excessive_timestamp_skew_flagged_even_when_angles_agree(self):
        values=run_skill('sensor-fusion-doa-imu-baseline',
            {**BASE,'acoustic_timestamp_s':1.0})['values']
        self.assertAlmostEqual(values['timestamp_skew_s'],1.0)
        self.assertEqual(values['disposition'],'EXCESSIVE_TIMESTAMP_SKEW')
        self.assertFalse(values['checks'][0]['passed'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'imu_heading_std_deg':0.0},{'acoustic_doa_std_deg':0.0},
                           {'imu_heading_deg':float('nan')},{'imu_heading_std_deg':True},
                           {'imu_heading_deg':400.0},{'max_acceptable_timestamp_skew_s':-1.0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('sensor-fusion-doa-imu-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
