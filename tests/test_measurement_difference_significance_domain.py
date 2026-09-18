"""Independent worked decisions for the two-measurement significance
z-score baseline, not a matched-conditions guarantee or a full
statistical study."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'measurement_1':85.0,'uncertainty_1':0.5,'measurement_2':83.0,'uncertainty_2':0.5,'significance_z_threshold':2.0}


class MeasurementDifferenceSignificanceDomainTests(unittest.TestCase):
    def test_tight_uncertainty_large_difference_is_significant(self):
        values=run_skill('measurement-difference-significance-baseline',BASE)['values']
        self.assertAlmostEqual(values['z_score'],2.82842712474619)
        self.assertTrue(values['statistically_significant'])
        self.assertEqual(values['disposition'],'DIFFERENCE_STATISTICALLY_SIGNIFICANT')

    def test_loose_uncertainty_small_difference_is_within_noise(self):
        values=run_skill('measurement-difference-significance-baseline',
            {'measurement_1':85.0,'uncertainty_1':2.0,'measurement_2':84.0,'uncertainty_2':2.0,'significance_z_threshold':2.0})['values']
        self.assertAlmostEqual(values['z_score'],0.35355339059327373)
        self.assertFalse(values['statistically_significant'])
        self.assertEqual(values['disposition'],'DIFFERENCE_WITHIN_MEASUREMENT_NOISE')

    def test_swapping_measurements_flips_sign_not_magnitude(self):
        values=run_skill('measurement-difference-significance-baseline',
            {**BASE,'measurement_1':83.0,'measurement_2':85.0})['values']
        self.assertAlmostEqual(values['z_score'],-2.82842712474619)
        self.assertTrue(values['statistically_significant'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'uncertainty_1':0.0},{'significance_z_threshold':0.0},
                           {'uncertainty_2':True},{'measurement_1':float('nan')}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('measurement-difference-significance-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
