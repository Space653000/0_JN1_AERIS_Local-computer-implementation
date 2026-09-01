import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
