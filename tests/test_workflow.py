import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import aeris_runtime.audit as audit
import aeris_runtime.evidence as evidence
import aeris_runtime.skills_runtime as skills
import aeris_runtime.taskstate as taskstate
import aeris_runtime.verification as verification
import aeris_runtime.workflow as workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.inputs = root / "inputs"
        self.inputs.mkdir()
        self.csv = self.inputs / "fr.csv"
        self.csv.write_text("frequency_hz,level_db\n100,80\n200,81\n500,79\n1000,82\n2000,80\n", encoding="utf-8")
        self.patches = [
            patch.object(skills, "_ALLOWED_INPUT_ROOTS", (self.inputs,)),
            patch.object(taskstate, "TASK_ROOT", root / "tasks"),
            patch.object(evidence, "EVIDENCE_ROOT", root / "evidence"),
            patch.object(verification, "VERIFICATION_ROOT", root / "verification"),
            patch.object(workflow, "WORKFLOW_ROOT", root / "workflows"),
            patch.object(audit, "AUDIT_DIR", root / "audit"),
            patch.object(audit, "AUDIT_FILE", root / "audit" / "audit.jsonl"),
            patch.object(audit, "LEDGER_PATH", root / "audit" / "audit.jsonl"),
            patch.object(audit, "LOCK_FILE", root / "audit" / ".audit.lock"),
        ]
        for p in self.patches:
            p.start()
        self.event_patches = [
            patch.object(taskstate, "append_event", return_value={}),
            patch.object(evidence, "append_event", return_value={}),
            patch.object(verification, "append_event", return_value={}),
            patch.object(workflow, "append_event", return_value={}),
        ]
        for p in self.event_patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.event_patches):
            p.stop()
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_versioned_templates_reference_real_skills_and_are_not_fake_runs(self):
        templates = workflow.list_workflow_templates()
        self.assertEqual(len(templates), 3)
        self.assertEqual(len(workflow.list_workflows()), 0)
        self.assertTrue(all(t["execution_state"] == "EXECUTABLE_TEMPLATE_NOT_RUN" for t in templates))
        self.assertEqual(
            {t["skill_id"] for t in templates},
            {"measurement-import-validation", "frequency-response-analysis", "requirement-verification"},
        )

    def test_requirement_template_accepts_structured_requirement_input(self):
        wf = workflow.create_workflow_from_template(
            "WF-TPL-REQUIREMENT-VERIFICATION",
            "Codex",
            summary="Verify FR flatness from template",
            description="speaker frequency response requirement",
            skill_params={
                "input_path": str(self.csv),
                "requirement": {"band_hz": [100, 2000], "max_peak_to_peak_db": 4.0},
            },
        )
        self.assertEqual(wf["workflow_template_id"], "WF-TPL-REQUIREMENT-VERIFICATION")
        self.assertEqual(wf["execution"]["skill_id"], "requirement-verification")
        self.assertEqual(wf["risk"], "R1")

    def test_template_refuses_missing_required_input(self):
        with self.assertRaisesRegex(ValueError, "missing required inputs"):
            workflow.create_workflow_from_template(
                "WF-TPL-REQUIREMENT-VERIFICATION",
                "Codex",
                skill_params={"input_path": str(self.csv)},
            )

    def test_deterministic_skill_reaches_evidenced_not_verified(self):
        wf = workflow.create_engineering_workflow(
            "Verify FR flatness",
            "Codex",
            description="speaker frequency response requirement",
            risk="R1",
            skill_id="requirement-verification",
            skill_params={
                "input_path": str(self.csv),
                "requirement": {"band_hz": [100, 2000], "max_peak_to_peak_db": 4.0},
            },
        )
        result = workflow.execute_workflow(wf["workflow_id"], "Codex")
        task = taskstate.load_task(result["task_id"])
        gates = verification.gate_summary(result["task_id"])
        self.assertEqual(result["state"], "EVIDENCED")
        self.assertEqual(task["state"], "EVIDENCED")
        self.assertEqual(gates["outcomes"]["G0_CONTRACT"], "PASS")
        self.assertEqual(gates["outcomes"]["G1_NUMERICAL"], "PASS")
        self.assertEqual(gates["outcomes"]["G2_DOMAIN"], "NOT_RUN")
        self.assertFalse(gates["g0_g4_passed"])
        self.assertTrue(evidence.validate_bundle(result["execution"]["run_id"])["valid"])

    def test_workflow_without_skill_blocks_instead_of_faking_execution(self):
        wf = workflow.create_engineering_workflow("Unknown task", "Codex", description="needs a tool")
        result = workflow.execute_workflow(wf["workflow_id"], "Codex")
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(taskstate.load_task(result["task_id"])["state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
