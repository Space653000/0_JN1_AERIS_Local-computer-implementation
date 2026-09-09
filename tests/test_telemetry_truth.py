import unittest
import threading
import time


class TelemetryTruthTests(unittest.TestCase):
    def test_request_during_an_older_collection_is_coalesced_not_lost(self):
        from aeris_runtime.telemetry import TelemetryProjection
        entered=threading.Event(); release=threading.Event()
        def collect(summary):
            entered.set()
            if not release.wait(5): raise TimeoutError('test barrier')
            return {'services':[],'tasks':summary['tasks']}
        projection=TelemetryProjection(collect)
        projection.get({'projects':0,'tasks':0}); self.assertTrue(entered.wait(1))
        second=projection.get({'projects':0,'tasks':1})
        self.assertFalse(second['assessment_complete'])
        release.set(); self.assertTrue(projection.wait_for_refresh(2))
        current=projection.get({'projects':0,'tasks':1})
        self.assertTrue(current['assessment_complete'])
        self.assertEqual(current['tasks'],1)

    def test_slow_telemetry_is_nonblocking_and_expired_health_is_not_reused(self):
        from aeris_runtime.telemetry import TelemetryProjection
        entered=threading.Event(); release=threading.Event(); clock=[0.0]; fail=[False]
        def collect(summary):
            entered.set()
            if not release.wait(5): raise TimeoutError('synthetic stalled probe')
            if fail[0]: raise ValueError('synthetic unavailable probe')
            return {'services':[{'service':'synthetic probe','state':'HEALTHY'}],
                    'state_counts':{'HEALTHY':1},'planes':['CONTROL'],'truth':'synthetic test input'}
        projection=TelemetryProjection(collect,clock=lambda:clock[0])
        started=time.monotonic(); pending=projection.get({'tasks':0,'projects':0})
        self.assertLess(time.monotonic()-started,0.5)
        self.assertTrue(pending['refresh_in_progress'])
        self.assertTrue(all(s['state']=='CHECKING' for s in pending['services']))
        self.assertTrue(entered.wait(1))
        release.set(); self.assertTrue(projection.wait_for_refresh(2))
        current=projection.get({'tasks':0,'projects':0})
        self.assertEqual(current['services'][0]['state'],'HEALTHY')
        # A fresh snapshot for different task counts is not this request's truth.
        release.clear(); changed=projection.get({'tasks':1,'projects':0})
        self.assertTrue(all(s['state']=='CHECKING' for s in changed['services']))
        release.set(); self.assertTrue(projection.wait_for_refresh(2))
        clock[0]=11.0; release.clear(); fail[0]=True
        expired=projection.get({'tasks':1,'projects':0})
        self.assertTrue(all(s['state']=='CHECKING' for s in expired['services']))
        release.set(); self.assertTrue(projection.wait_for_refresh(2))
        failed=projection.get({'tasks':1,'projects':0})
        self.assertTrue(all(s['state']=='FAILED' for s in failed['services']))
        self.assertNotIn('HEALTHY',failed['state_counts'])

    def test_contract_registration_is_not_routing_execution(self):
        from aeris_runtime.telemetry import role_router_status
        snapshot={'total_roles':100,'maturity_counts':{'L0':0,'L1':100,'L2':0,'L3':0,'L4':0}}
        state=role_router_status(snapshot)
        self.assertEqual(state['state'],'DEGRADED')
        self.assertEqual(state['capability_maturity'],'CONTRACT_ONLY')
        self.assertIn('contracted_roles=100',state['reason'])
        self.assertIn('domain_execution_roles=0',state['reason'])
        self.assertNotIn('100 executable',state['reason'])
        snapshot['maturity_counts'].update(L1=99,L2=1)
        state=role_router_status(snapshot)
        self.assertEqual(state['state'],'DEGRADED')
        self.assertIn('domain_execution_roles=1',state['reason'])
        self.assertIn('role_domain_accepted=0',state['reason'])
        self.assertEqual(state['capability_maturity'],'PARTIAL_DOMAIN_EXECUTION')

    def test_missing_or_inconsistent_counts_are_not_healthy(self):
        from aeris_runtime.telemetry import role_router_status
        for snapshot in ({},{'total_roles':100,'maturity_counts':{'L0':0,'L1':100,'L2':100,'L3':0,'L4':0}}):
            with self.assertRaises(ValueError): role_router_status(snapshot)


if __name__=='__main__': unittest.main()
