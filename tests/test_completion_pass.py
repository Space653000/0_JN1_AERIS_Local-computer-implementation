import unittest
from unittest.mock import patch

from aeris_runtime import completion
from aeris_runtime.completion import assess


class CompletionPassTests(unittest.TestCase):
    def test_report_has_required_autopilot_truth_fields(self):
        result=assess()
        for field in ("unresolved_software_gaps", "remaining_external_blockers", "remote_write_performed", "local_only_scope"):
            self.assertIn(field,result)
        self.assertFalse(result["remote_write_performed"])
        self.assertTrue(result["local_only_scope"])
        self.assertGreater(len(result["remaining_external_blockers"]),0)

    def test_declared_inventory_cannot_self_assert_complete(self):
        with patch.dict(completion.CHECKS, {"core_ui_ssot_six_pages": lambda: (False, "negative test")}, clear=False):
            result = assess()
        self.assertFalse(result["software_local_fixable_zero"])
        self.assertIn("core_ui_ssot_six_pages", {item["id"] for item in result["unresolved_software_gaps"]})


if __name__ == "__main__": unittest.main()
