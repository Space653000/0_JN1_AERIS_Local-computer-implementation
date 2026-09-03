import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from aeris_runtime import operations
from aeris_runtime.engineering import api, catalog
from aeris_runtime.engineering.orchestration import run_role


class EngineeringApiTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), operations._Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close(), self.thread.join()))

    def request(self, path, data=None, **headers):
        if data is not None:
            headers.setdefault('Content-Type', 'application/json')
        req = urllib.request.Request(self.base+path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    def test_capability_api_and_source_drift_fail_closed(self):
        with patch.object(api, 'live_matrix', return_value={'100_role_L2': 99}):
            status, result = self.request('/api/v1/capabilities')
            self.assertEqual((status, result['100_role_L2']), (200, 99))
        with patch.object(api, 'live_matrix', side_effect=RuntimeError('source changed')):
            self.assertEqual(self.request('/api/v1/capabilities')[0], 503)

    def test_remote_origin_host_and_form_rejected_before_mutation(self):
        with patch.object(api, 'post') as mutation:
            self.assertEqual(self.request('/api/v1/capabilities/execute', {}, Origin='https://evil.invalid')[0], 403)
            self.assertEqual(self.request('/api/v1/capabilities/execute', {}, Host='evil.invalid')[0], 403)
            self.assertEqual(self.request('/api/v1/capabilities/execute', {}, **{'Content-Type':'text/plain'})[0], 403)
            self.assertEqual(self.request('/api/v1/capabilities', Host='evil.invalid')[0], 403)
            mutation.assert_not_called()

    def test_authorized_json_dispatch_and_out_of_scope_fixture(self):
        with patch.object(api, 'post', return_value={'state':'EVIDENCED'}) as mutation:
            self.assertEqual(self.request('/api/v1/capabilities/execute', {'role_id':'R001'}, Origin=self.base)[0], 200)
            mutation.assert_called_once_with('/api/v1/capabilities/execute', {'role_id':'R001'})
        self.assertEqual(self.request('/api/v1/capabilities/fixture/R001?skill=unknown')[0], 400)

    def test_risk_and_calibration_cannot_be_self_asserted(self):
        params=catalog.definitions()['engineering-requirements']['fixture']['input']
        for options in ({'risk':'R3'}, {'source_kind':'CALIBRATED'}, {'context':{'risk':'R0'}}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                run_role('R001', 'engineering-requirements', params, objective='unsafe', **options)

    def test_supervisor_uses_engineering_environment_when_present(self):
        self.assertTrue(operations.supervisor_python())
        with patch('pathlib.Path.is_file', return_value=True):
            self.assertIn('.venv', operations.supervisor_python())

    def test_workspace_reuses_core_form_structure(self):
        script=(operations.ROOT/'ui'/'web'/'capabilities.js').read_text(encoding='utf-8')
        self.assertIn("form.className='formgrid'",script)
        self.assertIn("?'field full':'field'",script)
        self.assertIn("querySelector('#capOutput').className='code'",script)


if __name__ == '__main__':
    unittest.main()
