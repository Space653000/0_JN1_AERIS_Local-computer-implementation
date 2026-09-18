"""Independent worked decisions for the Glasberg & Moore (1990) ERB
auditory-filter baseline, not a listener preference or discomfort
judgment claim."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'center_frequency_hz':1000.0,'claimed_erb_hz':132.639,'max_acceptable_error_hz':1.0}


class ErbAuditoryFilterDomainTests(unittest.TestCase):
    def test_nominal_1khz_matches_independent_worked_calculation(self):
        values=run_skill('erb-auditory-filter-bandwidth-baseline',BASE)['values']
        self.assertAlmostEqual(values['predicted_erb_hz'],132.639)
        self.assertAlmostEqual(values['predicted_erb_rate'],15.621449713970488)
        self.assertTrue(values['model_applicable'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_outside_fitted_range_is_flagged(self):
        values=run_skill('erb-auditory-filter-bandwidth-baseline',
            {'center_frequency_hz':50.0,'claimed_erb_hz':40.0,'max_acceptable_error_hz':5.0})['values']
        self.assertFalse(values['model_applicable'])
        self.assertEqual(values['disposition'],'MODEL_OUTSIDE_FITTED_RANGE')

    def test_deviating_claim_is_flagged_not_silently_accepted(self):
        values=run_skill('erb-auditory-filter-bandwidth-baseline',
            {**BASE,'claimed_erb_hz':200.0,'max_acceptable_error_hz':5.0})['values']
        self.assertAlmostEqual(values['error_hz'],67.36099999999999)
        self.assertEqual(values['disposition'],'CLAIMED_BANDWIDTH_DEVIATES_FROM_ERB_MODEL')
        self.assertFalse(values['checks'][0]['passed'])

    def test_erb_grows_with_frequency(self):
        low=run_skill('erb-auditory-filter-bandwidth-baseline',{**BASE,'center_frequency_hz':250.0,'claimed_erb_hz':51.68475,'max_acceptable_error_hz':1.0})['values']
        high=run_skill('erb-auditory-filter-bandwidth-baseline',{**BASE,'center_frequency_hz':8000.0,'claimed_erb_hz':888.212,'max_acceptable_error_hz':1.0})['values']
        self.assertLess(low['predicted_erb_hz'],high['predicted_erb_hz'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'center_frequency_hz':0.0},{'center_frequency_hz':float('nan')},
                           {'claimed_erb_hz':-1.0},{'max_acceptable_error_hz':0.0},{'center_frequency_hz':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('erb-auditory-filter-bandwidth-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
