"""Independent worked decisions for the process-capability Cpk baseline,
not an empirical control-chart validation of statistical control."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'upper_spec_limit':10,'lower_spec_limit':0,'process_mean':5,'process_sigma':1,'minimum_acceptable_cpk':1.33}


class ProcessCapabilityCpkDomainTests(unittest.TestCase):
    def test_centered_process_cpk_matches_cpu_and_cpl(self):
        values=run_skill('process-capability-cpk-baseline',BASE)['values']
        self.assertAlmostEqual(values['cpu'],1.6666666666666667)
        self.assertAlmostEqual(values['cpl'],1.6666666666666667)
        self.assertAlmostEqual(values['cpk'],1.6666666666666667)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_offcenter_process_cpk_takes_constraining_side(self):
        values=run_skill('process-capability-cpk-baseline',{**BASE,'process_mean':8})['values']
        self.assertAlmostEqual(values['cpu'],0.6666666666666666)
        self.assertAlmostEqual(values['cpl'],2.6666666666666665)
        self.assertAlmostEqual(values['cpk'],0.6666666666666666)
        self.assertEqual(values['disposition'],'CPK_BELOW_MINIMUM_ACCEPTABLE')

    def test_tighter_sigma_improves_cpk(self):
        values=run_skill('process-capability-cpk-baseline',{**BASE,'process_sigma':0.5})['values']
        self.assertAlmostEqual(values['cpk'],3.3333333333333335)

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'upper_spec_limit':0,'lower_spec_limit':10},{'process_sigma':0},
                           {'minimum_acceptable_cpk':0},{'process_sigma':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('process-capability-cpk-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
