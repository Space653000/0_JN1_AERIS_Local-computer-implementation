import copy,unittest
from aeris_runtime import reproduction
from aeris_runtime.engineering import av_products,av_products_review,domain_review,role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state
BASE={"model":"SUPPLIED_MULTICHANNEL_LEVEL_POLARITY_DELAY_BUDGET","layout":"SEVEN_ONE_FOUR_DECLARED","physical_theater_verified":False,"channel_level_spread_db":1.0,"maximum_channel_level_spread_db":2.0,"polarity_error_count":0,"maximum_polarity_error_count":0,"channel_delay_error_ms":1.0,"maximum_channel_delay_error_ms":2.0,"seat_level_spread_db":3.0,"maximum_seat_level_spread_db":5.0,"subwoofer_crossover_error_db":1.0,"maximum_subwoofer_crossover_error_db":2.0,"calibration_position_count":6,"minimum_calibration_position_count":4}
class HomeTheaterTests(unittest.TestCase):
 def test_domains(self):self.assertEqual([c['id'] for c in av_products.analyze_theater(BASE)['checks']],['CHANNEL_LEVEL_MATCH','CHANNEL_POLARITY','CHANNEL_DELAY','SEAT_REGION_SPREAD','SUBWOOFER_CROSSOVER','CALIBRATION_POSITION_COVERAGE'])
 def test_fail_closed(self):
  self.assertFalse(av_products.analyze_theater({**BASE,'polarity_error_count':1})['checks'][1]['passed'])
  with self.assertRaises(ValueError):av_products.analyze_theater({**BASE,'physical_theater_verified':True})
 def test_review(self):
  c=av_products.analyze_theater(BASE);w=copy.deepcopy(c);w['wiring_verified']=True;self.assertEqual(av_products_review.review_theater(BASE,w)['decision'],'CHANGES_REQUIRED')
 def test_route(self):
  with isolated_engineering_state():
   f=role_acceptance.RoleAcceptanceFactory();self.assertTrue(f.evaluate('R057','home-theater-level-polarity-delay-baseline')['execution_passed']);self.assertTrue(f.evaluate('R026','home-theater-level-polarity-delay-domain-review')['execution_passed']);r=run_role('R057','home-theater-level-polarity-delay-baseline',BASE,objective='Bound theater architecture',source_kind='SYNTHETIC');self.assertEqual([x['role_id'] for x in r['pod']['reviewers']],['R026']);self.assertTrue(domain_review.review_status(r['review']['review_run_id'])['valid']);self.assertEqual(reproduction.reproduce_run(r['evidence_run_id'])['result'],'PASS')
