"""Independent worked decisions for the Delany-Bazley porous-absorber
baseline, not L4 or physical impedance-tube claims."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'flow_resistivity_pa_s_m2':20000.0,'thickness_m':0.025,'frequency_hz':1000.0,
      'minimum_target_absorption':0.2,'air_density_kg_m3':1.2,'sound_speed_m_s':343.0}


class PorousMaterialDomainTests(unittest.TestCase):
    def test_nominal_absorption_matches_independent_worked_calculation(self):
        out=run_skill('porous-material-absorption-baseline',BASE)
        values=out['values']
        self.assertAlmostEqual(values['normalized_frequency_parameter'],0.06)
        self.assertTrue(values['model_applicable'])
        self.assertAlmostEqual(values['absorption_coefficient'],0.3033752085072827)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertTrue(values['checks'][0]['passed'])
        self.assertFalse(out['physical_measurement_verified'])

    def test_boundary_at_x_equals_one_is_still_applicable(self):
        values=run_skill('porous-material-absorption-baseline',
            {**BASE,'flow_resistivity_pa_s_m2':1200.0,'minimum_target_absorption':0.01})['values']
        self.assertAlmostEqual(values['normalized_frequency_parameter'],1.0)
        self.assertTrue(values['model_applicable'])
        self.assertAlmostEqual(values['absorption_coefficient'],0.03183005658831428)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_just_outside_validated_range_is_flagged_not_silently_returned(self):
        values=run_skill('porous-material-absorption-baseline',
            {**BASE,'flow_resistivity_pa_s_m2':600.0})['values']
        self.assertAlmostEqual(values['normalized_frequency_parameter'],2.0)
        self.assertFalse(values['model_applicable'])
        self.assertEqual(values['disposition'],'MODEL_OUTSIDE_VALIDATED_RANGE')
        self.assertFalse(values['checks'][0]['passed'])

    def test_thin_sample_nonphysical_result_is_flagged_as_model_breakdown(self):
        """A negative absorption coefficient is a known Delany-Bazley
        limitation at thin/low-X extremes -- it must be surfaced as an
        honest model-breakdown disposition, never clamped to look like a
        real (if low) measured absorption value."""
        values=run_skill('porous-material-absorption-baseline',
            {**BASE,'thickness_m':0.005})['values']
        self.assertAlmostEqual(values['absorption_coefficient'],-0.04334059341758145)
        self.assertEqual(values['disposition'],'MODEL_RESULT_NONPHYSICAL_AT_THIS_THICKNESS_FREQUENCY')
        self.assertFalse(values['checks'][0]['passed'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'flow_resistivity_pa_s_m2':0.0},{'thickness_m':0.0},
                           {'flow_resistivity_pa_s_m2':True},{'frequency_hz':float('nan')},
                           {'minimum_target_absorption':1.5},{'minimum_target_absorption':-0.1},
                           {'air_density_kg_m3':0.5},{'sound_speed_m_s':1000.0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('porous-material-absorption-baseline',{**BASE,**overrides})

    def test_target_not_met_when_absorption_falls_short_of_declared_minimum(self):
        values=run_skill('porous-material-absorption-baseline',
            {**BASE,'minimum_target_absorption':0.9})['values']
        self.assertEqual(values['disposition'],'TARGET_NOT_MET')
        self.assertEqual(values['required_revisions'],['INCREASE_THICKNESS_OR_LOWER_FLOW_RESISTIVITY'])


if __name__=='__main__': unittest.main()
