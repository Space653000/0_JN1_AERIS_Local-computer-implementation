import json
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import aeris_runtime.controlplane as controlplane
import aeris_runtime.operations as operations
import aeris_runtime.workflow as workflow
from aeris_runtime import auth


class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.patches = [
            patch.object(controlplane, "DB_PATH", root / "control.sqlite3"),
            patch.object(workflow, "WORKFLOW_ROOT", root / "workflows"),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
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

    def _session_cookie(self):
        token = auth.create_session()
        self.addCleanup(auth.revoke_session, token)
        return f"{auth.SESSION_COOKIE_NAME}={token}"

    def _get_json(self, server, path, authenticated=True):
        request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}{path}")
        if authenticated:
            request.add_header("Cookie", self._session_cookie())
        with urllib.request.urlopen(request, timeout=3) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def test_ui_pages_have_no_inline_script_blocked_by_csp(self):
        # controlplane's Content-Security-Policy header sends script-src
        # 'self' with no 'unsafe-inline'/nonce, so any <script>...</script>
        # block (as opposed to <script src="...">) is silently blocked by
        # the browser -- the page renders its static shell forever and never
        # runs. progress.html shipped exactly this bug (an inline loader that
        # never executed); guard every served page against it.
        for path in (controlplane.UI_ROOT).glob("*.html"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"<script(?P<attrs>[^>]*)>(?P<body>[^<]*)</script>", text, re.IGNORECASE):
                if "src=" not in match.group("attrs") and match.group("body").strip():
                    self.fail(f"{path.name} has an inline <script> body; CSP script-src 'self' silently blocks it")

    def test_root_is_public_intro_not_dashboard(self):
        server = self._server()
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_charset(), "utf-8")
            self.assertIn("AERIS", body)
            self.assertIn("登入", body)

    def test_dashboard_requires_authentication(self):
        server = self._server()
        request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/dashboard")
        with urllib.request.urlopen(request, timeout=3) as response:
            # urlopen follows the 302 to /login automatically; assert we
            # actually landed on the login page, not the real dashboard.
            self.assertEqual(response.geturl(), f"http://127.0.0.1:{server.server_port}/login")
            self.assertIn("登入", response.read().decode("utf-8"))
        api_request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/api/v1/progress")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(api_request, timeout=3)
        self.assertEqual(ctx.exception.code, 401)

    def test_dashboard_is_real_dashboard_when_authenticated(self):
        server = self._server()
        request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/dashboard")
        request.add_header("Cookie", self._session_cookie())
        with urllib.request.urlopen(request, timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("本機聲學工程公司", body)
            self.assertIn("確定性 技能", body)
            self.assertIn("標準 登錄庫", body)
            self.assertIn("/assets/app.js", body)

    def test_roles_api_returns_100(self):
        server = self._server()
        data = self._get_json(server, "/api/v1/roles")
        self.assertEqual(data["count"], 100)
        self.assertEqual(data["roles"][0]["id"], "R001")

    def test_workflow_template_api_is_versioned_and_not_fake_run_count(self):
        server = self._server()
        data = self._get_json(server, "/api/v1/workflow-templates")
        self.assertEqual(data["count"], 3)
        self.assertTrue(all(x["execution_state"] == "EXECUTABLE_TEMPLATE_NOT_RUN" for x in data["templates"]))
        runs = self._get_json(server, "/api/v1/workflows")
        self.assertEqual(runs["workflows"], [])

    def test_skills_standards_and_expected_run_apis_are_real(self):
        server = self._server()
        skills = self._get_json(server, "/api/v1/skills")
        self.assertGreaterEqual(len(skills["skills"]), 3)
        standards = self._get_json(server, "/api/v1/standards?q=IEC")
        self.assertIn("standards", standards)
        health = self._get_json(server, "/api/v1/expected-runs")
        self.assertIn(health["overall"], {"HEALTHY", "DEGRADED", "FAILED", "NOT_CONFIGURED"})

    def test_five_plane_service_api_has_truth_fields(self):
        server = self._server()
        data = self._get_json(server, "/api/v1/services")
        from aeris_runtime.telemetry import wait_for_service_telemetry
        # Collection time scales with the local evidence store's real size
        # (validate_bundle runs once per sealed RUN- directory, plus a full
        # audit-ledger hash-chain walk); a large local store can take well
        # over 15s, so this bound is generous rather than tuned to an
        # artificially small fixture store.
        self.assertTrue(wait_for_service_telemetry(90))
        data = self._get_json(server, "/api/v1/services")
        self.assertTrue(data['assessment_complete'],
                        {k:data.get(k) for k in ('state_counts','snapshot_age_s','refresh_in_progress')})
        # Quiesce any follow-up refresh before fixture filesystem patches end.
        self.assertTrue(wait_for_service_telemetry(90))
        self.assertEqual(data["planes"], ["CONTROL", "KNOWLEDGE", "EXECUTION", "TRUST", "OPERATIONS"])
        self.assertGreaterEqual(len(data["services"]), 15)
        for service in data["services"]:
            for field in ("state", "reason", "evidence_ref", "last_update_utc", "capability_maturity"):
                self.assertIn(field, service)
        self.assertIn("process-alive alone is insufficient", data["truth"])

    def test_project_and_task_sqlite_roundtrip(self):
        store = controlplane.ControlStore()
        project = store.create_project("Acoustic EVT")
        task = store.create_task(project_id=project["id"], title="Speaker FR", description="Verify FR and distortion", risk_level="R1")
        self.assertEqual(task["project_id"], project["id"])
        self.assertEqual(task["state"], "DRAFT")
        self.assertEqual(len(store.list_tasks(project["id"])), 1)

    def test_workspace_metadata_and_workflow_link_roundtrip(self):
        store = controlplane.ControlStore()
        project = store.create_project("Workspace Contract")
        metadata = {"product": "Laptop", "transducer": "both", "lifecycle": "EVT", "evidence_tier": "Tier-B", "standards_strategy": "Internal", "requirement": "FR", "hypothesis": "leakage", "evidence_needed": "measurement"}
        task = store.create_task(project_id=project["id"], title="Workspace fields", description="FR", risk_level="R1", workflow_id="WF-TEST", metadata=metadata)
        self.assertEqual(task["workflow_id"], "WF-TEST")
        self.assertEqual(task["metadata"], metadata)


if __name__ == "__main__":
    unittest.main()
