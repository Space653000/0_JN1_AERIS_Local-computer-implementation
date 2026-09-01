import unittest

from aeris_runtime.standards_registry import list_standards, require_formal_use, search_standards


class StandardsRegistryTests(unittest.TestCase):
    def test_seed_registry_is_discoverable(self):
        items = list_standards()
        self.assertGreaterEqual(len(items), 6)
        self.assertTrue(any(x["standard_id"] == "IEC 60268-4" for x in items))
        self.assertTrue(search_standards("microphone"))

    def test_unverified_standard_cannot_be_used_formally(self):
        with self.assertRaises(RuntimeError):
            require_formal_use("IEC 60268-4")


if __name__ == "__main__":
    unittest.main()
