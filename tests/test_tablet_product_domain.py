import copy
import unittest

from aeris_runtime import reproduction
from aeris_runtime.engineering import domain_review,personal_device_products,personal_device_products_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_TABLET_ORIENTATION_CASE_TABLE_BUDGET","placement_set":"PORTRAIT_LANDSCAPE_TABLE","physical_tablet_verified":False,"orientation_mode_count":4,"minimum_orientation_mode_count":4,"blocked_edge_port_count":0,"maximum_blocked_edge_port_count":0,"case_port_clearance_mm":2.0,"minimum_case_port_clearance_mm":1.0,"table_reflection_delay_ms":3.0,"minimum_table_reflection_delay_ms":2.0,"stereo_balance_error_db":1.0,"maximum_stereo_balance_error_db":2.0,"array_steering_error_deg":5.0,"maximum_array_steering_error_deg":10.0}

class TabletProductTests(unittest.TestCase):
    def test_orientation_case_and_table_are_distinct(self):
        result=personal_device_products.analyze_tablet(BASE)
        self.assertEqual([c['id'] for c in result['checks']],['ORIENTATION_MODE_COVERAGE','CASE_BLOCKED_EDGE_PORTS','CASE_PORT_CLEARANCE','TABLE_REFLECTION_DELAY','STEREO_BALANCE','ARRAY_STEERING'])
        self.assertFalse(result['table_reflection_verified'])
    def test_case_block_and_physical_claim_fail_closed(self):
        self.assertFalse(personal_device_products.analyze_tablet({**BASE,'blocked_edge_port_count':1})['checks'][1]['passed'])
        with self.assertRaises(ValueError):personal_device_products.analyze_tablet({**BASE,'physical_tablet_verified':True})
    def test_reviewer_rejects_transfer_overclaim(self):
        candidate=personal_device_products.analyze_tablet(BASE);self.assertEqual(personal_device_products_review.review_tablet(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        wrong=copy.deepcopy(candidate);wrong['table_reflection_verified']=True
        self.assertEqual(personal_device_products_review.review_tablet(BASE,wrong)['decision'],'CHANGES_REQUIRED')
    def test_r052_routes_to_exact_r072_reviewer(self):
        with isolated_engineering_state():
            factory=role_acceptance.RoleAcceptanceFactory();self.assertTrue(factory.evaluate('R052','tablet-orientation-case-table-baseline')['execution_passed']);self.assertTrue(factory.evaluate('R072','tablet-orientation-case-table-domain-review')['execution_passed'])
            result=run_role('R052','tablet-orientation-case-table-baseline',BASE,objective='Bound tablet orientation and case architecture',source_kind='SYNTHETIC')
            self.assertEqual(result['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([r['role_id'] for r in result['pod']['reviewers']],['R072']);self.assertTrue(domain_review.review_status(result['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(result['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
