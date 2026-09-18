"""Independent worked decisions for the CLT-based test-automation
runtime-budget baseline, not a measured real-CI runtime distribution."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'mean_test_duration_s':2,'std_test_duration_s':0.5,'number_of_tests':100,'sigma_margin':3.0,'maximum_allowed_timeout_s':300}


class TestAutomationRuntimeBudgetDomainTests(unittest.TestCase):
    def test_recommended_timeout_fits_generous_budget(self):
        values=run_skill('test-automation-runtime-budget-baseline',BASE)['values']
        self.assertAlmostEqual(values['total_mean_s'],200)
        self.assertAlmostEqual(values['total_std_s'],5.0)
        self.assertAlmostEqual(values['recommended_timeout_s'],215.0)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_recommended_timeout_exceeds_tight_budget(self):
        values=run_skill('test-automation-runtime-budget-baseline',{**BASE,'maximum_allowed_timeout_s':210})['values']
        self.assertAlmostEqual(values['recommended_timeout_s'],215.0)
        self.assertEqual(values['disposition'],'RECOMMENDED_TIMEOUT_EXCEEDS_ALLOWED_BUDGET')
        self.assertFalse(values['checks'][0]['passed'])

    def test_std_scales_with_sqrt_of_test_count(self):
        values=run_skill('test-automation-runtime-budget-baseline',{**BASE,'number_of_tests':400})['values']
        self.assertAlmostEqual(values['total_std_s'],10.0)
        self.assertAlmostEqual(values['total_mean_s'],800)

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'mean_test_duration_s':0},{'std_test_duration_s':-1},
                           {'number_of_tests':0},{'number_of_tests':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('test-automation-runtime-budget-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
