"""Independent worked decisions for the Wilson score accuracy-interval
baseline, not a generalization or deployment-distribution guarantee."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'correct_predictions':95,'total_predictions':100,'minimum_acceptable_lower_bound':0.85}


class WilsonScoreAccuracyIntervalDomainTests(unittest.TestCase):
    def test_large_n_high_accuracy_is_supported(self):
        values=run_skill('wilson-score-accuracy-interval-baseline',BASE)['values']
        self.assertAlmostEqual(values['point_accuracy'],0.95)
        self.assertAlmostEqual(values['ci95_low'],0.8882495307680808)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_small_n_same_point_accuracy_is_not_supported(self):
        values=run_skill('wilson-score-accuracy-interval-baseline',
            {'correct_predictions':9,'total_predictions':10,'minimum_acceptable_lower_bound':0.85})['values']
        self.assertAlmostEqual(values['ci95_low'],0.5958499732047615)
        self.assertEqual(values['disposition'],'ACCURACY_CLAIM_NOT_SUPPORTED_AT_THIS_TEST_SET_SIZE')

    def test_larger_n_narrows_the_interval(self):
        small=run_skill('wilson-score-accuracy-interval-baseline',BASE)['values']
        large=run_skill('wilson-score-accuracy-interval-baseline',{'correct_predictions':950,'total_predictions':1000,'minimum_acceptable_lower_bound':0.85})['values']
        self.assertLess(large['ci95_high']-large['ci95_low'],small['ci95_high']-small['ci95_low'])

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'correct_predictions':101},{'total_predictions':0},{'correct_predictions':-1},{'total_predictions':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('wilson-score-accuracy-interval-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
