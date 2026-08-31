import unittest
from aeris_runtime.company import validate_company_manifest

class CompanyImageTests(unittest.TestCase):
    def test_company_manifest_contract(self):
        status = validate_company_manifest()
        self.assertTrue(status.valid, status.errors)
        self.assertEqual(status.company_id, "AERIS")
        self.assertEqual(status.role_count, 100)
        self.assertEqual(set(status.modes), {"offline", "local", "cloud", "auto"})

if __name__ == "__main__":
    unittest.main()
