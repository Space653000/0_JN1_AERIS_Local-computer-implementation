import unittest

from aeris_runtime.roles import get_role, list_roles, plan_pod


class RoleBaselineTests(unittest.TestCase):
    def test_registry_exposes_exactly_100_callable_seats(self):
        roles = list_roles()
        self.assertEqual(len(roles), 100)
        self.assertEqual(roles[0]["id"], "R001")
        self.assertEqual(roles[-1]["id"], "R100")
        self.assertTrue(all(r["execution_state"] == "CALLABLE_BASELINE_NOT_DOMAIN_VERIFIED" for r in roles))

    def test_mic_query_selects_microphone_specialists_and_chief(self):
        pod = plan_pod("麥克風遠場 beamforming AEC 降噪問題", 8)
        ids = {r["id"] for r in pod["roles"]}
        groups = {r["group"] for r in pod["roles"]}
        self.assertIn("R001", ids)
        self.assertIn("Microphone CoE", groups)
        self.assertGreaterEqual(pod["pod_size"], 2)
        self.assertLessEqual(pod["pod_size"], 8)

    def test_role_lookup_supports_numeric_or_canonical_id(self):
        self.assertEqual(get_role(1)["id"], "R001")
        self.assertEqual(get_role("R100")["index"], 100)


if __name__ == "__main__":
    unittest.main()
