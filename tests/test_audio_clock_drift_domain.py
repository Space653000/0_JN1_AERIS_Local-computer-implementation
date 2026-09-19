"""Independent worked decisions for the audio clock-drift buffer-margin
baseline, not measured real-hardware clock behavior or continuous-ASRC
verification claims."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'nominal_sample_rate_hz':48000,'source_clock_ppm_error':50,'sink_clock_ppm_error':-50,
      'buffer_size_samples':512,'resync_interval_s':10}


class AudioClockDriftDomainTests(unittest.TestCase):
    def test_short_interval_stays_within_half_buffer_margin(self):
        values=run_skill('audio-clock-drift-buffer-margin-baseline',BASE)['values']
        self.assertAlmostEqual(values['relative_ppm_error'],100)
        self.assertAlmostEqual(values['drift_rate_samples_per_s'],4.8)
        self.assertAlmostEqual(values['accumulated_drift_samples'],48.0)
        self.assertAlmostEqual(values['margin_samples'],208.0)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_long_interval_exceeds_margin_before_resync(self):
        values=run_skill('audio-clock-drift-buffer-margin-baseline',{**BASE,'resync_interval_s':200})['values']
        self.assertAlmostEqual(values['accumulated_drift_samples'],960.0)
        self.assertAlmostEqual(values['margin_samples'],-704.0)
        self.assertEqual(values['disposition'],'BUFFER_MARGIN_EXCEEDED_BEFORE_RESYNC')
        self.assertFalse(values['checks'][0]['passed'])

    def test_time_to_exhaust_is_self_consistent_with_accumulated_drift(self):
        values=run_skill('audio-clock-drift-buffer-margin-baseline',BASE)['values']
        exhaust=values['time_to_exhaust_half_buffer_s']
        at_exhaust=run_skill('audio-clock-drift-buffer-margin-baseline',{**BASE,'resync_interval_s':exhaust})['values']
        self.assertAlmostEqual(at_exhaust['margin_samples'],0.0,places=6)

    def test_matched_clocks_give_zero_drift_regardless_of_interval(self):
        values=run_skill('audio-clock-drift-buffer-margin-baseline',
            {**BASE,'source_clock_ppm_error':20,'sink_clock_ppm_error':20,'resync_interval_s':3600})['values']
        self.assertAlmostEqual(values['relative_ppm_error'],0)
        self.assertAlmostEqual(values['drift_rate_samples_per_s'],0)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in (
            {'nominal_sample_rate_hz':0},
            {'nominal_sample_rate_hz':-48000},
            {'nominal_sample_rate_hz':float('nan')},
            {'buffer_size_samples':0},
            {'buffer_size_samples':512.5},
            {'resync_interval_s':0},
            {'resync_interval_s':float('inf')},
            {'source_clock_ppm_error':600},
            {'sink_clock_ppm_error':-600},
            {'nominal_sample_rate_hz':True},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('audio-clock-drift-buffer-margin-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
