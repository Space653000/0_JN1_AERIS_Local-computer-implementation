"""Independent worked decisions for the DOE two-sample sample-size
baseline, not a pilot-validated experimental design."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'assumed_standard_deviation':5,'minimum_detectable_difference':2,'significance_level_alpha':0.05,
      'statistical_power':0.8,'maximum_affordable_sample_size_per_group':200}


class DoeTwoSampleSizeDomainTests(unittest.TestCase):
    def test_nominal_matches_independent_worked_calculation(self):
        values=run_skill('doe-two-sample-size-baseline',BASE)['values']
        self.assertAlmostEqual(values['z_alpha_half'],1.9599639845400536)
        self.assertAlmostEqual(values['z_beta'],0.8416212335729144)
        self.assertAlmostEqual(values['required_n_per_group_exact'],98.11099667936357)
        self.assertEqual(values['required_n_per_group'],99)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_tight_budget_flags_shortfall(self):
        values=run_skill('doe-two-sample-size-baseline',{**BASE,'maximum_affordable_sample_size_per_group':50})['values']
        self.assertEqual(values['required_n_per_group'],99)
        self.assertFalse(values['affordable'])
        self.assertEqual(values['disposition'],'REQUIRED_SAMPLE_SIZE_EXCEEDS_BUDGET')

    def test_higher_power_requires_more_samples(self):
        values=run_skill('doe-two-sample-size-baseline',
            {'assumed_standard_deviation':1,'minimum_detectable_difference':1,'significance_level_alpha':0.05,
             'statistical_power':0.9,'maximum_affordable_sample_size_per_group':30})['values']
        self.assertAlmostEqual(values['z_beta'],1.2815515655446008)
        self.assertAlmostEqual(values['required_n_per_group_exact'],21.014846122881238)
        self.assertEqual(values['required_n_per_group'],22)

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'assumed_standard_deviation':0},{'significance_level_alpha':1.0},
                           {'statistical_power':0.0},{'maximum_affordable_sample_size_per_group':1}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('doe-two-sample-size-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
