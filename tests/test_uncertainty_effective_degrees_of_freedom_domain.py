"""Independent worked decisions for the Welch-Satterthwaite effective
degrees of freedom baseline, not a Student's-t coverage-factor lookup."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'uncertainty_components':[0.1,0.2,0.05],'component_degrees_of_freedom':[10,5,60],'target_confidence_level':0.95}


class UncertaintyEffectiveDegreesOfFreedomDomainTests(unittest.TestCase):
    def test_modest_dof_components_land_in_small_sample_regime(self):
        values=run_skill('uncertainty-effective-degrees-of-freedom-baseline',BASE)['values']
        self.assertAlmostEqual(values['combined_standard_uncertainty'],0.22912878474779202)
        self.assertAlmostEqual(values['effective_degrees_of_freedom'],8.349637109498266)
        self.assertTrue(values['small_sample_regime'])
        self.assertEqual(values['disposition'],'SMALL_SAMPLE_REGIME_USE_STUDENT_T_COVERAGE_FACTOR')

    def test_large_dof_components_are_adequate_for_k2(self):
        values=run_skill('uncertainty-effective-degrees-of-freedom-baseline',
            {'uncertainty_components':[0.1,0.1],'component_degrees_of_freedom':[1000,1000],'target_confidence_level':0.95})['values']
        self.assertAlmostEqual(values['effective_degrees_of_freedom'],2000.0,places=6)
        self.assertFalse(values['small_sample_regime'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_single_component_dof_reduces_to_its_own_value(self):
        values=run_skill('uncertainty-effective-degrees-of-freedom-baseline',
            {'uncertainty_components':[0.15],'component_degrees_of_freedom':[12],'target_confidence_level':0.95})['values']
        self.assertAlmostEqual(values['effective_degrees_of_freedom'],12.0)

    def test_invalid_or_misaligned_inputs_are_rejected(self):
        for overrides in ({'uncertainty_components':[]},{'component_degrees_of_freedom':[10]},
                           {'target_confidence_level':1.0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('uncertainty-effective-degrees-of-freedom-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
