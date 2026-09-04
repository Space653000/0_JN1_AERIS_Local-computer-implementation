"""Speaker measurement decisions, not interpolation or a full-band certificate."""
import unittest
import copy
from aeris_runtime.engineering import speaker_fr
from aeris_runtime.engineering import role_acceptance,domain_review
from aeris_runtime.skills_runtime import run_skill
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state

BASE={
    'frequency_hz':[100,200,1000], 'spl_db':[80,80,80],
    'lower_mask_db':[78,78,78], 'upper_mask_db':[82,82,82],
    'distance_m':2, 'distance_lower_m':2, 'distance_upper_m':2, 'reference_distance_m':1,
    'drive_voltage_v':2, 'drive_lower_v':2, 'drive_upper_v':2, 'reference_voltage_v':1,
    'level_bound_db':1, 'gate_seconds':0.02, 'minimum_cycles':2,
    'propagation_model':'FREE_FIELD_FAR_FIELD',
    'drive_model':'LINEAR_SMALL_SIGNAL_SAME_CONFIG_NO_LIMITER',
}


class SpeakerFrDomainTests(unittest.TestCase):
    def test_review_rejects_false_experiment_cycles_and_statistical_claims(self):
        params={**BASE,'gate_seconds':0.005}
        original=run_skill('speaker-fr-reference-baseline',params)
        context={'product':'','transducer':'Speaker','lifecycle':'EVT','risk':'R1','source_kind':'SYNTHETIC'}
        for field,value in (
            ('next_discriminating_experiment','APPLY_BASS_EQ_TO_FIX_PROVEN_PRODUCT_DEFICIT'),
            ('observable_cycles',[999,999,999]),
            ('model_assumptions',['95% statistical confidence interval; normalization proves measured linearity']),
            ('scope','Full-band certified product measurement'),
            ('unresolved',[])):
            output=copy.deepcopy(original); output['values'][field]=value
            reviewed=run_skill('speaker-fr-uncertainty-domain-review',{
                'parameters':params,'candidate':domain_review._candidate('speaker-fr-uncertainty',output),'context':context})
            with self.subTest(field=field): self.assertEqual(reviewed['values']['decision'],'CHANGES_REQUIRED')

    def test_exact_cycle_boundary_survives_float_representation(self):
        params={**BASE,'frequency_hz':[1.9,200,1000],'gate_seconds':2/1.9}
        output=run_skill('speaker-fr-reference-baseline',params)
        self.assertTrue(output['values']['checks'][0]['passed'])
        candidate=domain_review._candidate('speaker-fr-uncertainty',output)
        context={'product':'','transducer':'Speaker','lifecycle':'EVT','risk':'R1','source_kind':'SYNTHETIC'}
        review=run_skill('speaker-fr-uncertainty-domain-review',{'parameters':params,'candidate':candidate,'context':context})
        self.assertEqual(review['values']['decision'],'BOUNDED_REVIEW_ACCEPT')

    def test_distance_and_voltage_reference_cancel_without_physical_claim(self):
        out=speaker_fr.analyze(BASE)
        self.assertEqual(out['normalized_spl_db'],[80,80,80])
        self.assertEqual(out['lower_interval_db'],[79,79,79])
        self.assertEqual(out['upper_interval_db'],[81,81,81])
        self.assertEqual(out['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertFalse(out['full_band_conformance_verified'])
        self.assertFalse(out['linearity_measured'])

    def test_reference_sign_and_uncertainty_propagation_change_decision(self):
        distance=speaker_fr.analyze({**BASE,'reference_voltage_v':2})
        self.assertAlmostEqual(distance['normalized_spl_db'][0],86.02059991327963)
        voltage=speaker_fr.analyze({**BASE,'reference_distance_m':2})
        self.assertAlmostEqual(voltage['normalized_spl_db'][0],73.97940008672037)
        uncertain=speaker_fr.analyze({**BASE,'distance_lower_m':1.8,'distance_upper_m':2.2,
                                     'drive_lower_v':1.8,'drive_upper_v':2.2})
        self.assertEqual(uncertain['normalized_spl_db'],[80,80,80])
        self.assertAlmostEqual(uncertain['lower_interval_db'][0],77.25699648562199)
        self.assertAlmostEqual(uncertain['upper_interval_db'][0],82.74300351437801)
        self.assertEqual(uncertain['sample_decisions'],['UNCERTAINTY_CROSSING']*3)

    def test_short_window_does_not_prove_a_low_frequency_product_failure(self):
        short=speaker_fr.analyze({**BASE,'gate_seconds':0.005})
        self.assertEqual(short['sample_decisions'],['INSUFFICIENT_MEASUREMENT_VALIDITY']*2+['WITHIN_SAMPLED_ENVELOPE'])
        self.assertEqual(short['next_discriminating_experiment'],'EXTEND_VALID_WINDOW_OR_USE_A_DIFFERENT_MEASUREMENT_METHOD')
        self.assertEqual(short['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_invalid_references_units_models_and_masks_are_rejected(self):
        for change in ({'distance_lower_m':0},{'drive_upper_v':1},{'frequency_hz':[100,100,1000]},
                       {'spl_db':[80]},{'upper_mask_db':[77,82,82]},{'gate_seconds':0},
                       {'minimum_cycles':True},{'spl_db':[80,float('nan'),80]},
                       {'propagation_model':'NEAR_FIELD'}, {'drive_model':'UNKNOWN'},
                       {'drive_model':'LIMITER_ACTIVE'}, {'voltage_dbv':6}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                speaker_fr.analyze({**BASE,**change})

    def test_separate_seat_suites_and_actual_reviewed_workflow(self):
        with isolated_engineering_state():
            runner=role_acceptance.RoleAcceptanceFactory()
            for role in ('R015','R079'):
                result=runner.evaluate(role)
                self.assertTrue(result['execution_passed'],result)
            rejected=run_role('R015','speaker-fr-reference-baseline',{**BASE,'gate_seconds':0.005},
                              objective='Short window cannot prove FR requirement',source_kind='SYNTHETIC')
            self.assertEqual(rejected['review']['decision'],'DESIGN_REVISION_REQUIRED')
            accepted=run_role('R015','speaker-fr-reference-baseline',BASE,
                              objective='Valid supplied window and bounded reference',source_kind='SYNTHETIC')
            self.assertEqual(accepted['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual([r['role_id'] for r in accepted['pod']['reviewers']],['R079'])
            self.assertTrue(domain_review.review_status(accepted['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(accepted['evidence_run_id'])['result'],'PASS')


if __name__=='__main__': unittest.main()
