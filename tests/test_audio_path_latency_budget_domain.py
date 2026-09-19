"""Independent worked decisions for the audio path latency-budget
baseline, not a measured end-to-end latency on real hardware/network."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'encode_delay_ms':20,'packetization_delay_ms':20,'network_one_way_delay_ms':40,
      'jitter_buffer_delay_ms':60,'decode_delay_ms':5,'output_buffer_delay_ms':10}


class AudioPathLatencyBudgetDomainTests(unittest.TestCase):
    def test_total_latency_exceeds_g114_by_5ms(self):
        values=run_skill('audio-path-latency-budget-baseline',BASE)['values']
        self.assertAlmostEqual(values['total_one_way_latency_ms'],155)
        self.assertAlmostEqual(values['itu_t_g114_threshold_ms'],150.0)
        self.assertEqual(values['disposition'],'LATENCY_EXCEEDS_ITU_T_G114_RECOMMENDATION')
        self.assertFalse(values['checks'][0]['passed'])

    def test_leaner_path_stays_within_g114(self):
        values=run_skill('audio-path-latency-budget-baseline',
            {'encode_delay_ms':10,'packetization_delay_ms':10,'network_one_way_delay_ms':30,
             'jitter_buffer_delay_ms':20,'decode_delay_ms':5,'output_buffer_delay_ms':5})['values']
        self.assertAlmostEqual(values['total_one_way_latency_ms'],80)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_breakdown_sums_to_total(self):
        values=run_skill('audio-path-latency-budget-baseline',BASE)['values']
        self.assertAlmostEqual(sum(values['component_breakdown_ms'].values()),values['total_one_way_latency_ms'])

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'encode_delay_ms':-1},{'network_one_way_delay_ms':float('nan')},{'decode_delay_ms':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('audio-path-latency-budget-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
