"""Independent worked decisions for the Arrhenius reliability
acceleration-factor baseline, not an empirically fitted activation
energy or failure-mechanism confirmation."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'activation_energy_ev':0.7,'use_temperature_c':25,'stress_temperature_c':85,'test_duration_hours':1000}


class ArrheniusAccelerationFactorDomainTests(unittest.TestCase):
    def test_nominal_matches_independent_worked_calculation(self):
        values=run_skill('arrhenius-acceleration-factor-baseline',BASE)['values']
        self.assertAlmostEqual(values['acceleration_factor'],95.99784604708066)
        self.assertAlmostEqual(values['equivalent_use_hours'],95997.84604708066,places=4)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_higher_stress_temperature_gives_larger_acceleration(self):
        values=run_skill('arrhenius-acceleration-factor-baseline',{**BASE,'stress_temperature_c':125})['values']
        self.assertAlmostEqual(values['acceleration_factor'],937.253649051674,places=4)

    def test_stress_at_or_below_use_temperature_is_rejected(self):
        for stress in (25,10):
            with self.subTest(stress=stress), self.assertRaises(ValueError):
                run_skill('arrhenius-acceleration-factor-baseline',{**BASE,'stress_temperature_c':stress})

    def test_minimal_delta_gives_acceleration_factor_near_one(self):
        values=run_skill('arrhenius-acceleration-factor-baseline',{**BASE,'stress_temperature_c':25.01})['values']
        self.assertAlmostEqual(values['acceleration_factor'],1.0,places=2)

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'activation_energy_ev':0.0},{'test_duration_hours':0.0},{'use_temperature_c':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('arrhenius-acceleration-factor-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
