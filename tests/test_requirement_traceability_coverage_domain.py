"""Independent worked decisions for the requirement traceability
coverage baseline, not an audit of link quality or test-pass status."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'total_requirements':100,'covered_requirements':85,'minimum_acceptable_coverage_percent':80}


class RequirementTraceabilityCoverageDomainTests(unittest.TestCase):
    def test_85_percent_coverage_meets_80_percent_minimum(self):
        values=run_skill('requirement-traceability-coverage-baseline',BASE)['values']
        self.assertAlmostEqual(values['coverage_percent'],85.0)
        self.assertEqual(values['uncovered_count'],15)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_40_percent_coverage_fails_80_percent_minimum(self):
        values=run_skill('requirement-traceability-coverage-baseline',{**BASE,'covered_requirements':40})['values']
        self.assertAlmostEqual(values['coverage_percent'],40.0)
        self.assertEqual(values['disposition'],'COVERAGE_BELOW_MINIMUM_ACCEPTABLE')

    def test_full_coverage_gives_zero_uncovered(self):
        values=run_skill('requirement-traceability-coverage-baseline',{**BASE,'covered_requirements':100})['values']
        self.assertAlmostEqual(values['coverage_percent'],100.0)
        self.assertEqual(values['uncovered_count'],0)

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'covered_requirements':101},{'total_requirements':0},{'covered_requirements':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('requirement-traceability-coverage-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
