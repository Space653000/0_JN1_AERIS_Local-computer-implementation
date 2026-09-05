import copy
import unittest
from aeris_runtime.engineering import microphone_architecture,microphone_architecture_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_MICROPHONE_ARCHITECTURE","capsule_sensitivity_dbv_per_pa":-38.0,"port_insertion_loss_db":1.5,"minimum_system_sensitivity_dbv_per_pa":-42.0,"capsule_self_noise_spl_db":26.0,"maximum_self_noise_spl_db":30.0,"capsule_acoustic_overload_spl_db":130.0,"required_acoustic_overload_spl_db":120.0,"array_element_count":4,"minimum_array_element_count":4,"array_spacing_m":0.02,"maximum_operating_frequency_hz":8000.0,"sound_speed_m_s":343.0,"maximum_port_loss_db":2.0,"sensitivity_tolerance_db":1.0,"port_path_kind":"MESHED_PORT","array_geometry_kind":"LINEAR"}

class MicrophoneArchitectureTests(unittest.TestCase):
    def test_capsule_port_and_array_budgets_remain_distinct(self):
        r=microphone_architecture.analyze(BASE)
        self.assertEqual(r['system_sensitivity_lower_dbv_per_pa'],-40.5);self.assertEqual(r['spatial_alias_frequency_hz'],8575.0)
        self.assertEqual(r['disposition'],'BOUNDED_BASELINE_ACCEPT');self.assertFalse(r['array_performance_verified'])
    def test_port_loss_and_geometry_fail_closed(self):
        r=microphone_architecture.analyze({**BASE,'port_insertion_loss_db':3.1});checks={x['id']:x for x in r['checks']}
        self.assertFalse(checks['SYSTEM_SENSITIVITY']['passed']);self.assertFalse(checks['PORT_INSERTION_LOSS']['passed'])
        with self.assertRaises(ValueError):microphone_architecture.analyze({**BASE,'array_geometry_kind':'SINGLE_CAPSULE'})
        with self.assertRaises(ValueError):microphone_architecture.analyze({**BASE,'array_element_count':4.0})
    def test_independent_review_rejects_port_transfer_claim(self):
        c=microphone_architecture.analyze(BASE);self.assertEqual(microphone_architecture_review.review(BASE,c)['decision'],'BOUNDED_REVIEW_ACCEPT')
        wrong=copy.deepcopy(c);wrong['port_transfer_verified']=True;r=microphone_architecture_review.review(BASE,wrong)
        self.assertEqual(r['decision'],'CHANGES_REQUIRED');self.assertEqual(r['disagreements'][0]['field'],'port_transfer_verified')
    def test_r027_routes_to_exact_r039_acoustic_path_reviewer(self):
        with isolated_engineering_state():
            f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R027','microphone-architecture-baseline')['execution_passed']);self.assertTrue(f.evaluate('R039','microphone-architecture-acoustic-path-domain-review')['execution_passed'])
            r=run_role('R027','microphone-architecture-baseline',BASE,objective='Bound capsule port and array architecture',source_kind='SYNTHETIC')
            self.assertEqual(r['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R039'])
            self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
