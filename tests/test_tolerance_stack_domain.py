"""Independent worked decisions for the RSS/worst-case dimensional
tolerance stack-up baseline, not measured process capability (Cpk) or
physical assembled-sample verification claims."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'contributor_tolerances_mm':[0.1,0.15,0.05,0.2],'maximum_acceptable_gap_mm':0.4}


class ToleranceStackDomainTests(unittest.TestCase):
    def test_worst_case_fails_but_rss_passes_is_its_own_disposition(self):
        values=run_skill('tolerance-stack-rss-baseline',BASE)['values']
        self.assertAlmostEqual(values['worst_case_stack_mm'],0.5)
        self.assertAlmostEqual(values['rss_stack_mm'],0.2738612787525831)
        self.assertEqual(values['disposition'],'WITHIN_STATISTICAL_RSS_BUT_NOT_WORST_CASE')
        self.assertFalse(values['checks'][0]['passed'])
        self.assertTrue(values['checks'][1]['passed'])

    def test_rss_still_discriminates_below_worst_case_near_the_limit(self):
        values=run_skill('tolerance-stack-rss-baseline',
            {'contributor_tolerances_mm':[0.09,0.12,0.15],'maximum_acceptable_gap_mm':0.21313203435596426})['values']
        self.assertAlmostEqual(values['worst_case_stack_mm'],0.36)
        self.assertAlmostEqual(values['rss_stack_mm'],0.21213203435596426)
        self.assertEqual(values['disposition'],'WITHIN_STATISTICAL_RSS_BUT_NOT_WORST_CASE')

    def test_gross_tolerances_fail_even_statistically(self):
        values=run_skill('tolerance-stack-rss-baseline',
            {'contributor_tolerances_mm':[5,5,5],'maximum_acceptable_gap_mm':1.0})['values']
        self.assertAlmostEqual(values['worst_case_stack_mm'],15)
        self.assertAlmostEqual(values['rss_stack_mm'],8.660254037844387)
        self.assertEqual(values['disposition'],'TOLERANCE_STACK_EXCEEDS_SPEC_EVEN_STATISTICALLY')
        self.assertFalse(values['checks'][0]['passed'])
        self.assertFalse(values['checks'][1]['passed'])

    def test_comfortable_contributors_pass_both_checks(self):
        values=run_skill('tolerance-stack-rss-baseline',
            {'contributor_tolerances_mm':[0.05,0.05],'maximum_acceptable_gap_mm':1.0})['values']
        self.assertAlmostEqual(values['worst_case_stack_mm'],0.1)
        self.assertAlmostEqual(values['rss_stack_mm'],0.07071067811865477)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in (
            {'contributor_tolerances_mm':[0.1]},
            {'contributor_tolerances_mm':[]},
            {'contributor_tolerances_mm':[0.1,-0.1]},
            {'contributor_tolerances_mm':[0.1,0.0]},
            {'contributor_tolerances_mm':[0.1,20.0]},
            {'contributor_tolerances_mm':[0.1,float('nan')]},
            {'contributor_tolerances_mm':[0.1,True]},
            {'maximum_acceptable_gap_mm':0.0},
            {'maximum_acceptable_gap_mm':-1.0},
            {'maximum_acceptable_gap_mm':float('inf')},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('tolerance-stack-rss-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
