"""Independent worked decisions for the Shannon-Nyquist sampling-check
baseline, not a spectral measurement of actual aliasing."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'sample_rate_hz':44100,'max_signal_frequency_hz':20000}


class NyquistSamplingCheckDomainTests(unittest.TestCase):
    def test_standard_audio_rate_satisfies_nyquist(self):
        values=run_skill('nyquist-sampling-check-baseline',BASE)['values']
        self.assertAlmostEqual(values['nyquist_frequency_hz'],22050.0)
        self.assertTrue(values['satisfies_nyquist'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_undersampled_rate_violates_nyquist(self):
        values=run_skill('nyquist-sampling-check-baseline',{**BASE,'sample_rate_hz':8000})['values']
        self.assertAlmostEqual(values['nyquist_frequency_hz'],4000.0)
        self.assertFalse(values['satisfies_nyquist'])
        self.assertEqual(values['disposition'],'ALIASING_RISK_NYQUIST_CRITERION_VIOLATED')

    def test_exact_boundary_at_twice_max_frequency_is_satisfied(self):
        values=run_skill('nyquist-sampling-check-baseline',{**BASE,'sample_rate_hz':40000})['values']
        self.assertAlmostEqual(values['nyquist_frequency_hz'],20000.0)
        self.assertTrue(values['satisfies_nyquist'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'sample_rate_hz':0},{'max_signal_frequency_hz':float('nan')},{'sample_rate_hz':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('nyquist-sampling-check-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
