"""Independent worked decisions for the Johnson-Nyquist thermal noise
floor baseline, not a full EMI/ground-loop root-cause diagnosis."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'resistance_ohm':10000.0,'temperature_c':25.0,'bandwidth_hz':20000.0,'claimed_noise_floor_v_rms':1.8146966674350842e-06}


class ThermalNoiseFloorDomainTests(unittest.TestCase):
    def test_nominal_10kohm_matches_independent_worked_calculation(self):
        values=run_skill('thermal-noise-floor-baseline',BASE)['values']
        self.assertAlmostEqual(values['thermal_floor_v_rms'],1.8146966674350842e-06)
        self.assertTrue(values['physically_consistent'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_excess_noise_above_thermal_is_flagged_as_likely_non_thermal(self):
        values=run_skill('thermal-noise-floor-baseline',
            {**BASE,'resistance_ohm':1000.0,'claimed_noise_floor_v_rms':0.001})['values']
        self.assertTrue(values['physically_consistent'])
        self.assertEqual(values['disposition'],'EXCESS_NOISE_LIKELY_NON_THERMAL_SOURCE')

    def test_claim_below_thermal_floor_is_physically_impossible(self):
        values=run_skill('thermal-noise-floor-baseline',{**BASE,'claimed_noise_floor_v_rms':1e-9})['values']
        self.assertFalse(values['physically_consistent'])
        self.assertEqual(values['disposition'],'CLAIMED_NOISE_BELOW_THERMAL_FLOOR_IMPOSSIBLE')
        self.assertFalse(values['checks'][0]['passed'])

    def test_higher_resistance_gives_higher_thermal_floor(self):
        low=run_skill('thermal-noise-floor-baseline',{**BASE,'resistance_ohm':1000.0,'claimed_noise_floor_v_rms':1.0})['values']
        high=run_skill('thermal-noise-floor-baseline',{**BASE,'resistance_ohm':100000.0,'claimed_noise_floor_v_rms':1.0})['values']
        self.assertLess(low['thermal_floor_v_rms'],high['thermal_floor_v_rms'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'resistance_ohm':0.0},{'temperature_c':-500.0},{'bandwidth_hz':-1.0},
                           {'claimed_noise_floor_v_rms':0.0},{'resistance_ohm':True},{'bandwidth_hz':float('nan')}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('thermal-noise-floor-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
