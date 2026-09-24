"""Independent worked decisions for the Bonferroni multiple-comparisons
correction baseline, not a full literature review."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'family_wise_alpha':0.05,'number_of_hypotheses_tested':1,'claimed_p_value':0.03}


class BonferroniSignificanceCorrectionDomainTests(unittest.TestCase):
    def test_single_hypothesis_survives_unchanged_threshold(self):
        values=run_skill('bonferroni-significance-correction-baseline',BASE)['values']
        self.assertAlmostEqual(values['adjusted_alpha'],0.05)
        self.assertTrue(values['survives_correction'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_twenty_hypotheses_fails_stricter_threshold(self):
        values=run_skill('bonferroni-significance-correction-baseline',{**BASE,'number_of_hypotheses_tested':20})['values']
        self.assertAlmostEqual(values['adjusted_alpha'],0.0025)
        self.assertFalse(values['survives_correction'])
        self.assertEqual(values['disposition'],'RESULT_NOT_SIGNIFICANT_AFTER_MULTIPLE_COMPARISONS_CORRECTION')

    def test_more_hypotheses_gives_stricter_linear_threshold(self):
        values=run_skill('bonferroni-significance-correction-baseline',{**BASE,'number_of_hypotheses_tested':40})['values']
        self.assertAlmostEqual(values['adjusted_alpha'],0.00125)

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'family_wise_alpha':1.0},{'number_of_hypotheses_tested':0},
                           {'claimed_p_value':1.0},{'number_of_hypotheses_tested':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('bonferroni-significance-correction-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
