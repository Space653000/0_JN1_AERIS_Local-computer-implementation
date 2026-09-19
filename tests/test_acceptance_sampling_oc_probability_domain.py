"""Independent worked decisions for the binomial acceptance-sampling OC
probability baseline, not a full producer/consumer risk study."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'sample_size':50,'acceptance_number':1,'assumed_defect_rate':0.01,'minimum_acceptable_probability_of_acceptance':0.9}


class AcceptanceSamplingOcProbabilityDomainTests(unittest.TestCase):
    def test_good_lot_is_usually_accepted(self):
        values=run_skill('acceptance-sampling-oc-probability-baseline',BASE)['values']
        self.assertAlmostEqual(values['probability_of_acceptance'],0.9105646869039689)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_bad_lot_is_usually_rejected(self):
        values=run_skill('acceptance-sampling-oc-probability-baseline',{**BASE,'assumed_defect_rate':0.05})['values']
        self.assertAlmostEqual(values['probability_of_acceptance'],0.27943175232069517)
        self.assertEqual(values['disposition'],'SAMPLING_PLAN_REJECTS_TOO_OFTEN_AT_THIS_DEFECT_RATE')

    def test_zero_defect_rate_gives_certain_acceptance(self):
        values=run_skill('acceptance-sampling-oc-probability-baseline',{**BASE,'assumed_defect_rate':0.0})['values']
        self.assertAlmostEqual(values['probability_of_acceptance'],1.0)

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'acceptance_number':60},{'assumed_defect_rate':-0.1},{'sample_size':0},{'sample_size':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('acceptance-sampling-oc-probability-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
