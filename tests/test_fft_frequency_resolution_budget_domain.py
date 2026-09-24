"""Independent worked decisions for the FFT frequency-resolution
planning baseline, not an executed instrument measurement."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'sample_rate_hz':48000,'planned_record_samples':4096,'target_frequency_resolution_hz':20}


class FftFrequencyResolutionBudgetDomainTests(unittest.TestCase):
    def test_record_meets_loose_target_resolution(self):
        values=run_skill('fft-frequency-resolution-budget-baseline',BASE)['values']
        self.assertAlmostEqual(values['actual_resolution_hz'],11.71875)
        self.assertTrue(values['meets_target'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_record_fails_tight_target_resolution(self):
        values=run_skill('fft-frequency-resolution-budget-baseline',{**BASE,'target_frequency_resolution_hz':1})['values']
        self.assertAlmostEqual(values['minimum_record_length_for_target_s'],1.0)
        self.assertFalse(values['meets_target'])
        self.assertEqual(values['disposition'],'PLANNED_RECORD_TOO_SHORT_FOR_TARGET_RESOLUTION')

    def test_doubling_record_length_halves_resolution_figure(self):
        values=run_skill('fft-frequency-resolution-budget-baseline',{**BASE,'planned_record_samples':8192})['values']
        self.assertAlmostEqual(values['actual_resolution_hz'],5.859375)

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'sample_rate_hz':0},{'planned_record_samples':1},
                           {'target_frequency_resolution_hz':0},{'planned_record_samples':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('fft-frequency-resolution-budget-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
