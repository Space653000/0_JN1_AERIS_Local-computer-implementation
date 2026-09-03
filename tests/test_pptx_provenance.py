import unittest

from aeris_runtime.pptx_provenance import verify


class PptxProvenanceTests(unittest.TestCase):
    def test_source_and_unsigned_executable_are_truthfully_provenanced(self):
        result = verify()
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["provenance_valid"])
        self.assertEqual(result["authenticode"], "NOT_SIGNED")
        self.assertEqual(result["production_acceptance"], "NOT_RUN_NO_INPUT_PPTX")
        self.assertTrue(all(item["actual_sha256"] == item["expected_sha256"] for item in result["checks"]))


if __name__ == "__main__":
    unittest.main()
