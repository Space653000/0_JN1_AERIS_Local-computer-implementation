import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import taskstate


class TaskStateTests(unittest.TestCase):
    def test_forbidden_shortcut_is_rejected(self):
        with tempfile.TemporaryDirectory() as td, patch.object(taskstate, "TASK_ROOT", Path(td)), patch.object(taskstate, "append_event"):
            task = taskstate.create_task("test", "Codex", task_id="T1")
            self.assertEqual(task["state"], "DRAFT")
            with self.assertRaises(ValueError):
                taskstate.transition_task("T1", "VERIFIED", "Codex", evidence_refs=["evidence://1"], authority="Codex")

    def test_evidence_and_human_authority_are_required(self):
        with tempfile.TemporaryDirectory() as td, patch.object(taskstate, "TASK_ROOT", Path(td)), patch.object(taskstate, "append_event"):
            taskstate.create_task("test", "Codex", task_id="T2")
            taskstate.transition_task("T2", "READY", "Codex")
            taskstate.transition_task("T2", "EXECUTING", "Codex")
            taskstate.transition_task("T2", "EXECUTED", "Codex")
            with self.assertRaises(ValueError):
                taskstate.transition_task("T2", "EVIDENCED", "Codex")
            taskstate.transition_task("T2", "EVIDENCED", "Codex", evidence_refs=["run://1"])
            with self.assertRaises(ValueError):
                taskstate.transition_task("T2", "VERIFIED", "Reviewer", evidence_refs=["review://1"], authority="Independent Reviewer")
            with self.assertRaises(ValueError):
                taskstate.transition_task("T2", "APPROVED", "Codex", evidence_refs=["review://1"], authority="Codex")
            with self.assertRaises(ValueError):
                taskstate.transition_task("T2", "APPROVED", "Human", evidence_refs=["approval://1"], authority="Human Chief Engineer")
            self.assertEqual(taskstate.load_task("T2")["state"], "EVIDENCED")


if __name__ == "__main__":
    unittest.main()
