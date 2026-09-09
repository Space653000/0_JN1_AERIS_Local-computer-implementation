import copy
import unittest
from aeris_runtime import reproduction
from aeris_runtime.engineering import domain_review,overear_anc_product,overear_anc_product_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_OVER_EAR_ANC_SEAL_STABILITY","cushion_interface":"CIRCUMAURAL_FOAM","physical_fit_verified":False,"full_loop_stability_verified":False,"cushion_leak_pole_hz":50.0,"bass_reference_hz":100.0,"maximum_leak_loss_db":3.0,"fit_state_count":6,"minimum_fit_state_count":5,"feedback_crossover_hz":100.0,"feedback_delay_ms":1.0,"plant_phase_lag_deg":90.0,"minimum_phase_margin_deg":45.0,"driver_peak_excursion_mm":0.4,"safe_peak_excursion_mm":0.5,"cushion_compression_fraction":0.2,"maximum_cushion_compression_fraction":0.3,"earcup_pressure_proxy_pa":0.8,"maximum_earcup_pressure_proxy_pa":1.0}

class OverEarANCProductTests(unittest.TestCase):
    def test_fit_seal_feedback_and_pressure_are_distinct(self):
        r=overear_anc_product.analyze(BASE);self.assertAlmostEqual(r['cushion_leak_loss_db'],0.9691001300805642);self.assertEqual(r['feedback_phase_margin_deg'],54.0);self.assertFalse(r['pressure_sensation_verified'])
    def test_glasses_leak_and_physical_claim_fail_closed(self):
        self.assertFalse(overear_anc_product.analyze({**BASE,'cushion_leak_pole_hz':200.0})['checks'][1]['passed'])
        with self.assertRaises(ValueError):overear_anc_product.analyze({**BASE,'physical_fit_verified':True})
    def test_review_rejects_listener_overclaim(self):
        c=overear_anc_product.analyze(BASE);self.assertEqual(overear_anc_product_review.review(BASE,c)['decision'],'BOUNDED_REVIEW_ACCEPT');w=copy.deepcopy(c);w['pressure_sensation_verified']=True;self.assertEqual(overear_anc_product_review.review(BASE,w)['decision'],'CHANGES_REQUIRED')
    def test_r049_routes_to_exact_r005_overear_reviewer(self):
        with isolated_engineering_state():
            f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R049','over-ear-anc-seal-stability-baseline')['execution_passed']);self.assertTrue(f.evaluate('R005','over-ear-anc-seal-stability-domain-review')['execution_passed'])
            r=run_role('R049','over-ear-anc-seal-stability-baseline',BASE,objective='Bound circumaural fit and ANC stability',source_kind='SYNTHETIC')
            self.assertEqual(r['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R005']);self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
