import copy,unittest
from aeris_runtime import reproduction
from aeris_runtime.engineering import av_products,av_products_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state
BASE={"model":"SUPPLIED_SOUNDBAR_CROSSOVER_WALL_DIALOGUE_BUDGET","subwoofer_polarity":"NORMAL_DECLARED","physical_soundbar_verified":False,"crossover_sum_error_db":1.0,"maximum_crossover_sum_error_db":2.0,"subwoofer_delay_error_ms":1.0,"maximum_subwoofer_delay_error_ms":2.0,"wall_boundary_gain_db":3.0,"maximum_wall_boundary_gain_db":6.0,"dialogue_headroom_db":6.0,"minimum_dialogue_headroom_db":3.0,"lip_sync_error_ms":20.0,"maximum_lip_sync_error_ms":40.0,"seat_response_spread_db":4.0,"maximum_seat_response_spread_db":6.0}
class SoundbarTests(unittest.TestCase):
 def test_domains(self):self.assertEqual([c['id'] for c in av_products.analyze_soundbar(BASE)['checks']],['CROSSOVER_SUM','SUBWOOFER_DELAY','WALL_BOUNDARY_GAIN','DIALOGUE_HEADROOM','LIP_SYNC','SEAT_RESPONSE_SPREAD'])
 def test_fail_closed(self):
  self.assertFalse(av_products.analyze_soundbar({**BASE,'wall_boundary_gain_db':8.0})['checks'][2]['passed'])
  with self.assertRaises(ValueError):av_products.analyze_soundbar({**BASE,'physical_soundbar_verified':True})
 def test_review(self):
  c=av_products.analyze_soundbar(BASE);w=copy.deepcopy(c);w['lip_sync_perceptually_verified']=True;self.assertEqual(av_products_review.review_soundbar(BASE,w)['decision'],'CHANGES_REQUIRED')
 def test_route(self):
  with isolated_engineering_state():
   f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R056','soundbar-crossover-wall-dialogue-baseline')['execution_passed']);self.assertTrue(f.evaluate('R024','soundbar-crossover-wall-dialogue-domain-review')['execution_passed']);r=run_role('R056','soundbar-crossover-wall-dialogue-baseline',BASE,objective='Bound soundbar architecture',source_kind='SYNTHETIC');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R024']);self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')
