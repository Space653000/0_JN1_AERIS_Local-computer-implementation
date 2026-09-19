"""Independent worked decisions for the Woodworth spherical-head ITD
baseline, not L4 or individualized-HRTF-measurement claims."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'head_radius_m':0.0875,'sound_speed_m_s':343.0,'azimuth_deg':45.0,
      'claimed_itd_us':380.7,'max_acceptable_itd_error_us':5.0}


class BinauralItdDomainTests(unittest.TestCase):
    def test_nominal_45_degrees_matches_independent_worked_calculation(self):
        values=run_skill('binaural-itd-spherical-head-baseline',BASE)['values']
        self.assertAlmostEqual(values['predicted_itd_us'],380.7410572918356)
        self.assertAlmostEqual(values['itd_error_us'],0.041057291835613796)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_90_degree_maximum_matches_the_well_known_human_max_itd(self):
        """Not a fitted coincidence -- this is the same formula evaluated
        at its own maximum, and it lands on the commonly cited ~650-660
        microsecond figure for a typical head radius."""
        values=run_skill('binaural-itd-spherical-head-baseline',
            {**BASE,'azimuth_deg':90.0,'claimed_itd_us':655.8})['values']
        self.assertAlmostEqual(values['predicted_itd_us'],655.8153894884939)
        self.assertTrue(600<values['predicted_itd_us']<700)

    def test_front_back_symmetry_of_a_sphere_gives_identical_magnitude(self):
        front=run_skill('binaural-itd-spherical-head-baseline',BASE)['values']
        back=run_skill('binaural-itd-spherical-head-baseline',{**BASE,'azimuth_deg':135.0})['values']
        left=run_skill('binaural-itd-spherical-head-baseline',{**BASE,'azimuth_deg':-45.0})['values']
        self.assertAlmostEqual(front['predicted_itd_us'],back['predicted_itd_us'])
        self.assertAlmostEqual(front['predicted_itd_us'],left['predicted_itd_us'])

    def test_large_claimed_deviation_is_flagged_not_silently_accepted(self):
        values=run_skill('binaural-itd-spherical-head-baseline',{**BASE,'claimed_itd_us':500.0})['values']
        self.assertAlmostEqual(values['itd_error_us'],119.2589427081644)
        self.assertEqual(values['disposition'],'ITD_MISMATCH_EXCEEDS_TOLERANCE')
        self.assertFalse(values['checks'][0]['passed'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'head_radius_m':0.20},{'head_radius_m':0.0},
                           {'azimuth_deg':200.0},{'azimuth_deg':float('nan')},
                           {'max_acceptable_itd_error_us':0.0},{'sound_speed_m_s':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('binaural-itd-spherical-head-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
