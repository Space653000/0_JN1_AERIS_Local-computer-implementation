"""Independent pressure/voltage and 3-4-5 noise-budget worked examples."""
import unittest

from aeris_runtime.skills_runtime import run_skill

SKILL='microphone-reference-noise-headroom-baseline'
BASE={
    'calibrator_pressure_rms_pa':1.0,'calibrator_output_rms_v':0.1,
    'calibration_gain_linear':10.0,'analysis_gain_linear':10.0,
    'total_noise_rms_v':0.00001,'frontend_noise_rms_v':0.000006,'ambient_noise_rms_pa':0.0,
    'adc_peak_v':1.0,'required_spl_db':100.0,'signal_crest_factor':2.0,
    'minimum_sensitivity_dbv_per_pa':-42.0,'maximum_sensitivity_dbv_per_pa':-38.0,
    'maximum_self_noise_spl_db':20.0,'minimum_electrical_headroom_db':3.0,
    'pressure_relative_bound':0.0,'gain_relative_bound':0.0,'noise_relative_bound':0.0,
}


class MicrophoneMeasurementDomainTests(unittest.TestCase):
    def test_common_reference_noise_subtraction_and_headroom_are_distinct(self):
        out=run_skill(SKILL,BASE); values=out['values']
        self.assertAlmostEqual(values['sensitivity_dbv_per_pa'],-40.0)
        self.assertAlmostEqual(values['self_noise_rms_pa'],0.00008)
        self.assertAlmostEqual(values['self_noise_spl_db'],12.041199826559248)
        self.assertAlmostEqual(values['electrical_headroom_db'],7.958800173440752)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertFalse(values['capsule_overload_verified'])
        self.assertFalse(out['physical_measurement_verified'])

    def test_equal_unresolved_noise_requires_room_or_frontend_discrimination(self):
        frontend=run_skill(SKILL,{**BASE,'frontend_noise_rms_v':0.00001})['values']
        room=run_skill(SKILL,{**BASE,'frontend_noise_rms_v':0.0,'ambient_noise_rms_pa':0.0001})['values']
        for values in (frontend,room):
            self.assertFalse(values['noise_resolved'])
            self.assertIsNone(values['self_noise_spl_db'])
            self.assertEqual(values['disposition'],'DESIGN_REVISION_REQUIRED')
        self.assertEqual(frontend['next_discriminating_experiment'],'LOWER_NOISE_FRONTEND_AT_MATCHED_GAIN')
        self.assertEqual(room['next_discriminating_experiment'],'QUIETER_ROOM_OR_CALIBRATOR_COUPLING')

    def test_uncertainty_and_analysis_gain_cannot_be_hidden_by_nominal_sensitivity(self):
        uncertain=run_skill(SKILL,{**BASE,'noise_relative_bound':0.3})['values']
        self.assertFalse(uncertain['noise_resolved'])
        reference=run_skill(SKILL,{**BASE,'pressure_relative_bound':0.1,'minimum_sensitivity_dbv_per_pa':-40.0})['values']
        self.assertEqual(reference['sensitivity_dbv_per_pa'],-40.0)
        self.assertFalse(reference['checks'][0]['passed'])
        gain=run_skill(SKILL,{**BASE,'analysis_gain_linear':100.0})['values']
        self.assertEqual(gain['sensitivity_dbv_per_pa'],-40.0)
        self.assertAlmostEqual(gain['electrical_headroom_db'],-12.041199826559248)
        self.assertFalse(gain['capsule_overload_verified'])
        boundary=run_skill(SKILL,{**BASE,'minimum_sensitivity_dbv_per_pa':-40.0,'maximum_sensitivity_dbv_per_pa':-40.0})['values']
        self.assertTrue(boundary['checks'][0]['passed'])

    def test_reference_units_clipping_and_inconsistent_noise_fail_closed(self):
        for change in ({'calibrator_output_dbfs':-20.0},{'calibration_gain_linear':0.0},
                       {'calibrator_output_rms_v':1.0},{'frontend_noise_rms_v':0.001},
                       {'noise_relative_bound':float('nan')},{'analysis_gain_linear':True},
                       {'minimum_sensitivity_dbv_per_pa':-30.0}):
            with self.subTest(change=change),self.assertRaises(ValueError): run_skill(SKILL,{**BASE,**change})


if __name__=='__main__': unittest.main()
