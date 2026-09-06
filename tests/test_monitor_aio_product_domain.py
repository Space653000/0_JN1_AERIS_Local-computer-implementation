import copy
import unittest
from aeris_runtime import reproduction
from aeris_runtime.engineering import conference_products,conference_products_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_MONITOR_AIO_CONFERENCE_BUDGET","usb_mode":"USB_AUDIO_ASYNCHRONOUS_DECLARED","physical_monitor_verified":False,"power_supply_hum_db":-50.0,"maximum_power_supply_hum_db":-40.0,"bezel_array_spread_db":2.0,"maximum_bezel_array_spread_db":3.0,"desk_reflection_delay_ms":3.0,"minimum_desk_reflection_delay_ms":2.0,"usb_audio_latency_ms":20.0,"maximum_usb_audio_latency_ms":30.0,"display_orientation_count":4,"minimum_display_orientation_count":3,"echo_reference_alignment_ms":2.0,"maximum_echo_reference_alignment_ms":5.0}

class MonitorAIOProductTests(unittest.TestCase):
    def test_hum_usb_and_desk_are_distinct(self):
        r=conference_products.analyze_monitor(BASE);self.assertEqual([c['id'] for c in r['checks']],['POWER_SUPPLY_HUM','BEZEL_ARRAY_SPREAD','DESK_REFLECTION_DELAY','USB_AUDIO_LATENCY','DISPLAY_ORIENTATION_COVERAGE','ECHO_REFERENCE_ALIGNMENT']);self.assertFalse(r['hum_source_verified'])
    def test_hum_and_physical_claim_fail_closed(self):
        self.assertFalse(conference_products.analyze_monitor({**BASE,'power_supply_hum_db':-30.0})['checks'][0]['passed'])
        with self.assertRaises(ValueError):conference_products.analyze_monitor({**BASE,'physical_monitor_verified':True})
    def test_reviewer_rejects_source_overclaim(self):
        c=conference_products.analyze_monitor(BASE);self.assertEqual(conference_products_review.review_monitor(BASE,c)['decision'],'BOUNDED_REVIEW_ACCEPT');w=copy.deepcopy(c);w['hum_source_verified']=True;self.assertEqual(conference_products_review.review_monitor(BASE,w)['decision'],'CHANGES_REQUIRED')
    def test_r054_routes_to_r076(self):
        with isolated_engineering_state():
            f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R054','monitor-aio-usb-desk-baseline')['execution_passed']);self.assertTrue(f.evaluate('R076','monitor-aio-usb-desk-domain-review')['execution_passed']);r=run_role('R054','monitor-aio-usb-desk-baseline',BASE,objective='Bound monitor conference architecture',source_kind='SYNTHETIC');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R076']);self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
