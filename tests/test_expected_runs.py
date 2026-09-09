import tempfile
import unittest
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import aeris_runtime.expected_runs as er


class ExpectedRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "expected.json"
        self.patch = patch.object(er, "REGISTRY_PATH", self.path)
        self.audit = patch.object(er, "append_event", return_value={})
        self.patch.start(); self.audit.start()

    def tearDown(self):
        self.audit.stop(); self.patch.stop(); self.tmp.cleanup()

    def test_unconfigured_is_not_healthy(self):
        self.assertEqual(er.assess_all()["overall"], "NOT_CONFIGURED")

    def test_default_operational_contracts_are_initialized_without_fake_success(self):
        data = er.ensure_defaults(audit_event=False)
        runs = data["expected_runs"]
        self.assertEqual(set(runs), {"company-opening-assessment", "supervisor-heartbeat"})
        self.assertTrue(all(item["last_result"] is None for item in runs.values()))
        self.assertEqual(er.assess_all()["overall"], "DEGRADED")

    def test_ensure_defaults_preserves_existing_history(self):
        er.ensure_defaults(audit_event=False)
        er.mark("supervisor-heartbeat", True, audit_event=False)
        before = er._read()["expected_runs"]["supervisor-heartbeat"]["last_success_at_utc"]
        er.ensure_defaults(audit_event=False)
        after = er._read()["expected_runs"]["supervisor-heartbeat"]["last_success_at_utc"]
        self.assertEqual(before, after)

    def test_success_is_healthy_then_stale(self):
        er.register("nightly-index", max_age_sec=60)
        self.assertEqual(er.mark("nightly-index", True)["state"], "HEALTHY")
        data = er._read()
        data["expected_runs"]["nightly-index"]["last_success_at_utc"] = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
        er._write(data)
        self.assertEqual(er.assess_all()["runs"][0]["state"], "STALE")

    def test_latest_failure_is_failed(self):
        er.register("job", max_age_sec=60)
        er.mark("job", True)
        self.assertEqual(er.mark("job", False, error="boom")["state"], "FAILED")

    def test_transient_windows_replace_lock_does_not_drop_page(self):
        from aeris_runtime import operations
        er.ensure_defaults(audit_event=False)
        original=Path.replace
        failures=[]
        def busy_once(source,target):
            if target==self.path and not failures:
                failures.append(True)
                raise PermissionError(5,'simulated Windows reader sharing denial')
            return original(source,target)
        server=ThreadingHTTPServer(('127.0.0.1',0),operations._Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            with patch.object(operations,'_read_json',return_value={'operational_state':'OPEN_WITH_LIMITS'}), patch.object(operations,'HEARTBEAT_FILE',Path(self.tmp.name)/'heartbeat.json'), patch.object(Path,'replace',busy_once):
                with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/services?theme=light',timeout=5) as response:
                    self.assertEqual(response.status,200)
                    self.assertIn(b'/assets/aeris-live.js',response.read())
            self.assertEqual(failures,[True])
            self.assertEqual(er.assess_all()['runs'][1]['last_result'],'SUCCESS')
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_permanent_replace_denial_is_not_reported_as_success(self):
        er.ensure_defaults(audit_event=False)
        before=self.path.read_bytes()
        with patch.object(Path,'replace',side_effect=PermissionError(5,'persistent denial')), patch.object(er.time,'sleep'):
            with self.assertRaises(PermissionError): er.mark('supervisor-heartbeat',True,audit_event=False)
        self.assertEqual(self.path.read_bytes(),before)


if __name__ == "__main__":
    unittest.main()
