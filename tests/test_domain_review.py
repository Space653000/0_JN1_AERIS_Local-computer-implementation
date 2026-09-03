"""Review oracles are hand-worked candidate reports, not executor outputs."""
import copy
import unittest

from aeris_runtime.engineering import domain_review
from tests.test_speaker_power_domain import BASE
from tests.test_tws_domain_method import BASE as TWS_BASE


def thermal_input():
    return {'parameters':{**BASE,'duration_s':0.0},
            'candidate':{'predicted_coil_temperature_c':25.0,'compression_db':0.0,
                         'thermal_passed':True,'next_experiment':'HARMONIC_HEADROOM_SWEEP',
                         'physical_measurement_verified':False,'lifetime_verified':False},
            'context':{'product':'','transducer':'Speaker','lifecycle':'EVT','risk':'R1',
                       'source_kind':'SYNTHETIC'}}


class DomainReviewTests(unittest.TestCase):
    def test_thermal_reviewer_rejects_fabricated_temperature_and_lifetime(self):
        original=thermal_input()
        result=domain_review.review('speaker-thermal',original)
        self.assertEqual(result['decision'],'BOUNDED_REVIEW_ACCEPT')
        self.assertFalse(result['human_approval'])
        for change in ({'predicted_coil_temperature_c':35.0},{'lifetime_verified':True},
                       {'thermal_passed':False}):
            bad=copy.deepcopy(original); bad['candidate'].update(change)
            with self.subTest(change=change):
                self.assertEqual(domain_review.review('speaker-thermal',bad)['decision'],'CHANGES_REQUIRED')

    def test_thermal_review_distinguishes_cold_limiter_from_hot_compression(self):
        request=thermal_input()
        request['parameters'].update(fundamental_rms_pa=0.5,input_power_w=0.0)
        request['candidate'].update(compression_db=6.020599913279624,next_experiment='COLD_AMPLIFIER_LIMITER_CAPTURE')
        self.assertEqual(domain_review.review('speaker-thermal',request)['decision'],'BOUNDED_REVIEW_ACCEPT')
        request['parameters'].update(input_power_w=20.0,duration_s=100.0)
        request['candidate'].update(predicted_coil_temperature_c=151.42411176571153,thermal_passed=False)
        rejected=domain_review.review('speaker-thermal',request)
        self.assertEqual(rejected['disagreements'][0]['field'],'next_experiment')
        request['candidate']['next_experiment']='COOLING_RESISTANCE_SWEEP'
        self.assertEqual(domain_review.review('speaker-thermal',request)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_nonlinear_review_rejects_amplitude_sum_and_unproven_attribution(self):
        request=thermal_input(); request['parameters']['harmonic_rms_pa']=[0.03,0.04]
        request['candidate']={'thd_percent':5.0,'compression_db':0.0,'thd_passed':True,'compression_passed':True,
                              'transducer_cause_verified':False,'physical_measurement_verified':False,'lifetime_verified':False}
        self.assertEqual(domain_review.review('speaker-nonlinear',request)['decision'],'BOUNDED_REVIEW_ACCEPT')
        request['candidate']['thd_percent']=7.0
        self.assertEqual(domain_review.review('speaker-nonlinear',request)['decision'],'CHANGES_REQUIRED')
        request['candidate'].update(thd_percent=5.0,transducer_cause_verified=True)
        self.assertEqual(domain_review.review('speaker-nonlinear',request)['disagreements'][0]['field'],'transducer_cause_verified')

    def test_anc_review_respects_inclusive_margin_and_single_crossover_limit(self):
        request={'parameters':{**TWS_BASE,'feedback_delay_ms':1.25},
                 'context':{'product':'R048','transducer':'Both','lifecycle':'EVT','risk':'R1','source_kind':'SYNTHETIC'},
                 'candidate':{'phase_margin_deg':45.0,'feedback_passed':True,'feedforward_passed':True,
                              'anc_topology_candidate':'HYBRID','full_loop_stability_verified':False,
                              'physical_measurement_verified':False,'lifetime_verified':False}}
        self.assertEqual(domain_review.review('tws-anc',request)['decision'],'BOUNDED_REVIEW_ACCEPT')
        request['candidate']['full_loop_stability_verified']=True
        self.assertEqual(domain_review.review('tws-anc',request)['decision'],'CHANGES_REQUIRED')
        request['candidate']['full_loop_stability_verified']=False
        request['parameters']['ff_wind_rms_pa']=0.01
        self.assertEqual(domain_review.review('tws-anc',request)['decision'],'CHANGES_REQUIRED')
        request['candidate'].update(feedforward_passed=False,anc_topology_candidate='FB_ONLY')
        self.assertEqual(domain_review.review('tws-anc',request)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_fit_review_distinguishes_wind_from_ambient_at_equal_total_noise(self):
        request={'parameters':{**TWS_BASE,'leak_pole_hz':0.0,'call_ambient_rms_pa':0.003,'ff_wind_rms_pa':0.004},
                 'context':{'product':'R048','transducer':'Both','lifecycle':'EVT','risk':'R1','source_kind':'SYNTHETIC'},
                 'candidate':{'leak_loss_db':0.0,'call_snr_db':12.041199826559248,'seal_passed':True,
                     'capture_passed':False,'next_experiment':'WIND_SHIELD_AND_PORT_ORIENTATION',
                     'excursion_measured':False,'occlusion_measured':False,
                     'physical_measurement_verified':False,'lifetime_verified':False}}
        self.assertEqual(domain_review.review('tws-fit-capture',request)['decision'],'BOUNDED_REVIEW_ACCEPT')
        request['parameters'].update(call_ambient_rms_pa=0.004,ff_wind_rms_pa=0.003)
        self.assertEqual(domain_review.review('tws-fit-capture',request)['decision'],'CHANGES_REQUIRED')
        request['candidate']['next_experiment']='STATIONARY_NOISE_AND_CAPTURE_PATH'
        self.assertEqual(domain_review.review('tws-fit-capture',request)['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_review_rejects_wrong_units_malformed_claims_and_out_of_scope_context(self):
        for context in ({'risk':'R3'},{'lifecycle':'MP'},{'transducer':'Microphone'},{'source_kind':'CALIBRATED'}):
            request=thermal_input(); request['context'].update(context)
            with self.subTest(context=context),self.assertRaises(ValueError): domain_review.review('speaker-thermal',request)
        for values in ({'drive_voltage_dbv':6.0},{'harmonic_rms_pa':[]},{'input_power_w':True}):
            request=thermal_input(); request['parameters'].update(values)
            with self.subTest(values=values),self.assertRaises(ValueError): domain_review.review('speaker-thermal',request)
        request=thermal_input(); del request['candidate']['lifetime_verified']
        with self.assertRaises(ValueError): domain_review.review('speaker-thermal',request)


if __name__=='__main__': unittest.main()
