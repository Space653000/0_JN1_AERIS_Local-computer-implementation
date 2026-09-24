"""Independent worked decisions for the Fisher r-to-z correlation
statistical-support baseline, not a computed MOS prediction claim."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'claimed_correlation_r':0.85,'sample_size':30}


class CorrelationStatisticalSupportDomainTests(unittest.TestCase):
    def test_strong_large_n_is_statistically_supported(self):
        values=run_skill('correlation-statistical-support-baseline',BASE)['values']
        self.assertAlmostEqual(values['ci95_low_r'],0.7058967064069308)
        self.assertAlmostEqual(values['ci95_high_r'],0.9265369024703374)
        self.assertTrue(values['statistically_supported'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_weak_small_n_is_not_statistically_supported(self):
        values=run_skill('correlation-statistical-support-baseline',{'claimed_correlation_r':0.3,'sample_size':10})['values']
        self.assertAlmostEqual(values['ci95_low_r'],-0.4063880891085119)
        self.assertAlmostEqual(values['ci95_high_r'],0.7819293207681977)
        self.assertFalse(values['statistically_supported'])
        self.assertEqual(values['disposition'],'CORRELATION_NOT_STATISTICALLY_SUPPORTED_AT_THIS_SAMPLE_SIZE')

    def test_larger_sample_size_narrows_the_interval(self):
        small=run_skill('correlation-statistical-support-baseline',BASE)['values']
        large=run_skill('correlation-statistical-support-baseline',{**BASE,'sample_size':300})['values']
        self.assertLess(large['ci95_high_r']-large['ci95_low_r'],small['ci95_high_r']-small['ci95_low_r'])

    def test_invalid_or_boundary_inputs_are_rejected(self):
        for overrides in ({'claimed_correlation_r':1.0},{'claimed_correlation_r':-1.0},
                           {'sample_size':3},{'sample_size':True},{'claimed_correlation_r':float('nan')}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('correlation-statistical-support-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
