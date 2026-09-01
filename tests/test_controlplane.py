import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import aeris_runtime.controlplane as controlplane
import aeris_runtime.operations as operations


class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(controlplane, "DB_PATH", Path(self.tmp.name) / "control.sqlite3")
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()
        self.tmp.cleanup()

    def _server(self):
        opening = {
            "operational_state": "OPEN_WITH_LIMITS",
            "company_complete": False,
            "runtime_mode": "auto",
        }
        p1 = patch.object(operations, "assess_opening", return_value=opening)
        p2 = patch.object(operations, "_write_heartbeat", return_value=None)
        p1.start(); p2.start()
        server = ThreadingHTTPServer(("127.0.0.1", 0), operations._Handler)
        server.shutdown_token = "test-token"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), p2.stop(), p1.stop()))
        return server

    def _get_json(self, server, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}{path}", timeout=3) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def test_root_is_real_dashboard_not_404(self):
        server = self._server()
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("本機聲學工程公司", body)
            self.assertIn("Deterministic Skills", body)
            self.assertIn("Standards Registry", body)
            self.assertIn("/assets/app.js", body)

    def test_roles_api_returns_100(self):
        server = self._server()
        data = self._get_json(server, "/api/v1/roles")
        self.assertEqual(data["count"], 100)
        self.assertEqual(data["roles"][0]["id"], "R001")

    def test_skills_standards_and_expected_run_apis_are_real(self):
        server = self._server()
        skills = self._get_json(server, "/api/v1/skills")
        self.assertGreaterEqual(len(skills["skills"]), 3)
        standards = self._get_json(server, "/api/v1/standards?q=IEC")
        self.assertIn("standards", standards)
        health = self._get_json(server, "/api/v1/expected-runs")
        self.assertIn(health["overall"], {"HEALTHY", "DEGRADED", "FAILED", "NOT_CONFIGURED"})

    def test_project_and_task_sqlite_roundtrip(self):
        store = controlplane.ControlStore()
        project = store.create_project("Acoustic EVT")
        task = store.create_task(project_id=project["id"], title="Speaker FR", description="Verify FR and distortion", risk_level="R1")
        self.assertEqual(task["project_id"], project["id"])
        self.assertEqual(task["state"], "DRAFT")
        self.assertEqual(len(store.list_tasks(project["id"])), 1)


if __name__ == "__main__":
    unittest.main()
