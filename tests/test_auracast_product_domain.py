import copy
import unittest
from aeris_runtime import reproduction
from aeris_runtime.engineering import auracast_product,auracast_product_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

BASE={"model":"SUPPLIED_AURACAST_LATENCY_SYNC_BUDGET","codec_profile":"LC3_DECLARED","broadcast_profile":"PUBLIC_ASSISTIVE_LISTENING","audibility_verified":False,"interoperability_verified":False,"transmitter_buffer_ms":10.0,"codec_frame_ms":10.0,"transport_latency_ms":20.0,"receiver_buffer_ms":20.0,"receiver_processing_ms":10.0,"maximum_end_to_end_latency_ms":100.0,"maximum_receiver_clock_offset_ppm":50.0,"resync_interval_s":20.0,"maximum_inter_receiver_skew_ms":1.0,"receiver_count":4,"minimum_receiver_count":3,"packet_loss_fraction":0.01,"maximum_packet_loss_fraction":0.02,"receiver_level_spread_db":2.0,"maximum_receiver_level_spread_db":3.0}

class AuracastProductTests(unittest.TestCase):
    def test_latency_sync_and_receiver_diversity_are_distinct(self):
        r=auracast_product.analyze(BASE);self.assertEqual((r['end_to_end_latency_ms'],r['worst_resync_skew_ms']),(70.0,1.0));self.assertFalse(r['interoperability_verified'])
    def test_transport_and_interoperability_fail_closed(self):
        self.assertFalse(auracast_product.analyze({**BASE,'transport_latency_ms':60.0})['checks'][0]['passed'])
        with self.assertRaises(ValueError):auracast_product.analyze({**BASE,'interoperability_verified':True})
    def test_review_rejects_receiver_matrix_overclaim(self):
        c=auracast_product.analyze(BASE);self.assertEqual(auracast_product_review.review(BASE,c)['decision'],'BOUNDED_REVIEW_ACCEPT');w=copy.deepcopy(c);w['physical_receiver_matrix_verified']=True;self.assertEqual(auracast_product_review.review(BASE,w)['decision'],'CHANGES_REQUIRED')
    def test_r047_routes_to_exact_r081_transport_reviewer(self):
        with isolated_engineering_state():
            f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R047','auracast-latency-sync-baseline')['execution_passed']);self.assertTrue(f.evaluate('R081','auracast-transport-sync-domain-review')['execution_passed'])
            r=run_role('R047','auracast-latency-sync-baseline',BASE,objective='Bound Auracast transport and receiver sync',source_kind='SYNTHETIC')
            self.assertEqual(r['review']['decision'],'BOUNDED_REVIEW_ACCEPT');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R081']);self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')

if __name__=='__main__':unittest.main()
