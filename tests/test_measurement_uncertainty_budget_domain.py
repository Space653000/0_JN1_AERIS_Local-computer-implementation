"""Independent worked decisions for the GUM-style measurement
uncertainty-budget baseline, not an empirically validated gage R&R
study."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'uncertainty_components':[0.1,0.2,0.05],'coverage_factor':2.0,'maximum_acceptable_expanded_uncertainty':1.0}


class MeasurementUncertaintyBudgetDomainTests(unittest.TestCase):
    def test_modest_components_stay_within_budget(self):
        values=run_skill('measurement-uncertainty-budget-baseline',BASE)['values']
        self.assertAlmostEqual(values['combined_standard_uncertainty'],0.22912878474779202)
        self.assertAlmostEqual(values['expanded_uncertainty'],0.45825756949558405)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_larger_components_exceed_budget(self):
        values=run_skill('measurement-uncertainty-budget-baseline',{**BASE,'uncertainty_components':[0.5,0.5,0.5]})['values']
        self.assertAlmostEqual(values['combined_standard_uncertainty'],0.8660254037844386)
        self.assertAlmostEqual(values['expanded_uncertainty'],1.7320508075688772)
        self.assertEqual(values['disposition'],'EXPANDED_UNCERTAINTY_EXCEEDS_BUDGET')
        self.assertFalse(values['checks'][0]['passed'])

    def test_rss_stays_below_arithmetic_sum(self):
        values=run_skill('measurement-uncertainty-budget-baseline',BASE)['values']
        self.assertLess(values['combined_standard_uncertainty'],sum(BASE['uncertainty_components']))

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'uncertainty_components':[]},{'uncertainty_components':[-0.1]},
                           {'coverage_factor':0.5},{'maximum_acceptable_expanded_uncertainty':0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('measurement-uncertainty-budget-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
