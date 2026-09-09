"""Independent worked decisions for nonlinear/power validation, not L4 claims."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'reference_voltage_rms_v':1.0,'drive_voltage_rms_v':2.0,
      'reference_fundamental_rms_pa':0.5,'fundamental_rms_pa':1.0,'harmonic_rms_pa':[0.01,0.005],
      'input_power_w':1.0,'thermal_resistance_k_per_w':10.0,'thermal_capacity_j_per_k':10.0,
      'duration_s':100.0,'ambient_temperature_c':25.0,
      'max_thd_percent':5.0,'max_compression_db':3.0,'max_coil_temperature_c':80.0}


class SpeakerPowerDomainTests(unittest.TestCase):
    def test_equal_compression_requires_different_hot_and_cold_experiments(self):
        cold=run_skill('speaker-power-distortion-baseline',{**BASE,'fundamental_rms_pa':0.5,'input_power_w':0.0})['values']
        hot=run_skill('speaker-power-distortion-baseline',{**BASE,'fundamental_rms_pa':0.5,'input_power_w':20.0})['values']
        self.assertAlmostEqual(cold['compression_db'],6.020599913279624)
        self.assertEqual(cold['compression_db'],hot['compression_db'])
        self.assertAlmostEqual(hot['predicted_coil_temperature_c'],151.42411176571153)
        self.assertNotEqual(cold['next_discriminating_experiment'],hot['next_discriminating_experiment'])
        self.assertNotIn('REDUCE_DUTY_AND_RECHECK_COIL_TEMPERATURE',cold['required_revisions'])
        self.assertIn('REDUCE_DUTY_AND_RECHECK_COIL_TEMPERATURE',hot['required_revisions'])

    def test_invalid_units_zero_nonfinite_and_underflow_inputs_are_rejected(self):
        for values in ({'fundamental_rms_pa':0.0},{'drive_voltage_dbv':6.0},{'input_power_w':True},
                       {'harmonic_rms_pa':[]},{'harmonic_rms_pa':[float('nan')]},
                       {'thermal_capacity_j_per_k':1e-320},{'reference_voltage_rms_v':1e-320}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                run_skill('speaker-power-distortion-baseline',{**BASE,**values})

    def test_distortion_compression_and_thermal_limits_are_separate(self):
        out=run_skill('speaker-power-distortion-baseline',BASE)
        values=out['values']
        self.assertAlmostEqual(values['thd_percent'],1.118033988749895)
        self.assertAlmostEqual(values['compression_db'],0.0)
        self.assertAlmostEqual(values['predicted_coil_temperature_c'],31.32120558828558)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertFalse(out['physical_measurement_verified'])
        boundary=run_skill('speaker-power-distortion-baseline',{**BASE,'harmonic_rms_pa':[0.03,0.04]})['values']
        self.assertTrue(boundary['checks'][0]['passed'])
        high=run_skill('speaker-power-distortion-baseline',{**BASE,'harmonic_rms_pa':[0.1,0.0]})['values']
        self.assertEqual(high['required_revisions'],['LOWER_DRIVE_AND_DISCRIMINATE_TRANSDUCER_FROM_AMPLIFIER_NONLINEARITY'])
        self.assertEqual(high['disposition'],'DESIGN_REVISION_REQUIRED')


if __name__=='__main__': unittest.main()
