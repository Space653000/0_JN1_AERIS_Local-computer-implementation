import unittest

from aeris_runtime.completion import assess


class CompletionPassTests(unittest.TestCase):
    def test_report_has_required_autopilot_truth_fields(self):
        result=assess()
        for field in ("unresolved_software_gaps", "remaining_external_blockers", "remote_write_performed", "local_only_scope"):
            self.assertIn(field,result)
        self.assertFalse(result["remote_write_performed"])
        self.assertTrue(result["local_only_scope"])
        self.assertGreater(len(result["remaining_external_blockers"]),0)


if __name__ == "__main__": unittest.main()
