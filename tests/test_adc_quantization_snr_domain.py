"""Independent worked decisions for the ADC quantization SNR/ENOB
baseline, not a noise-shaping/oversampling-aware model."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'bit_depth':16,'claimed_sinad_db':95}


class AdcQuantizationSnrDomainTests(unittest.TestCase):
    def test_plausible_16bit_sinad_is_physically_consistent(self):
        values=run_skill('adc-quantization-snr-baseline',BASE)['values']
        self.assertAlmostEqual(values['ideal_snr_db'],98.08)
        self.assertAlmostEqual(values['effective_number_of_bits'],15.488372093023257)
        self.assertTrue(values['physically_consistent'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_24bit_ideal_snr_matches_known_reference(self):
        values=run_skill('adc-quantization-snr-baseline',{'bit_depth':24,'claimed_sinad_db':110})['values']
        self.assertAlmostEqual(values['ideal_snr_db'],146.23999999999998)
        self.assertTrue(values['physically_consistent'])

    def test_sinad_exceeding_ideal_limit_is_flagged_impossible(self):
        values=run_skill('adc-quantization-snr-baseline',{**BASE,'claimed_sinad_db':100})['values']
        self.assertFalse(values['physically_consistent'])
        self.assertEqual(values['disposition'],'CLAIMED_SINAD_EXCEEDS_IDEAL_QUANTIZATION_LIMIT')
        self.assertFalse(values['checks'][0]['passed'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'bit_depth':0},{'claimed_sinad_db':float('nan')},{'bit_depth':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('adc-quantization-snr-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
