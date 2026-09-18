"""Independent worked decisions for the FMEA Risk Priority Number
baseline, not a cross-functional team consensus verification."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'severity_rating':8,'occurrence_rating':5,'detection_rating':3,'maximum_acceptable_rpn':150}


class FmeaRiskPriorityNumberDomainTests(unittest.TestCase):
    def test_rpn_120_meets_150_threshold(self):
        values=run_skill('fmea-risk-priority-number-baseline',BASE)['values']
        self.assertEqual(values['rpn'],120)
        self.assertTrue(values['within_acceptable_rpn'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_maximum_possible_rpn_exceeds_tight_threshold(self):
        values=run_skill('fmea-risk-priority-number-baseline',
            {'severity_rating':10,'occurrence_rating':10,'detection_rating':10,'maximum_acceptable_rpn':500})['values']
        self.assertEqual(values['rpn'],1000)
        self.assertFalse(values['within_acceptable_rpn'])
        self.assertEqual(values['disposition'],'RPN_EXCEEDS_ACCEPTABLE_LIMIT')

    def test_minimum_possible_rpn_passes(self):
        values=run_skill('fmea-risk-priority-number-baseline',
            {**BASE,'severity_rating':1,'occurrence_rating':1,'detection_rating':1})['values']
        self.assertEqual(values['rpn'],1)
        self.assertTrue(values['within_acceptable_rpn'])

    def test_invalid_or_out_of_range_ratings_are_rejected(self):
        for overrides in ({'severity_rating':0},{'severity_rating':11},{'occurrence_rating':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('fmea-risk-priority-number-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
