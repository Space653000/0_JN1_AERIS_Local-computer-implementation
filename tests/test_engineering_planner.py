"""planner.plan_and_execute() is the first thing in the codebase that lets
step 2's skill choice depend on step 1's actual result. route_pod/run_role/
factory are mocked at the module's own import site (matching
test_engineering_intake.py's convention); catalog.definitions() is real,
cheap and deterministic, so skill-ID/required-input checks exercise the
genuine schema.
"""
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from aeris_runtime import audit
from aeris_runtime.config import ROOT
from aeris_runtime.engineering import planner

_TDOA_PARAMS = {
    "reference": [0.0], "delayed": [0.0], "sample_rate_hz": 48000,
    "spacing_m": 0.1, "sound_speed_m_s": 343,
}
_BEAMFORM_PARAMS = {
    "positions_m": [0, 0.02], "channels": [[0.0], [0.0]],
    "sample_rate_hz": 48000, "sound_speed_m_s": 343, "steering_deg": 0,
}


def _report(skill_id, state="EVIDENCED", values=None, project_id="PROJECT-1", run_id="RUN-1"):
    return {
        "project_id": project_id, "state": state,
        "numerical_result": {"skill_id": skill_id, "values": values or {}},
        "evidence_run_id": run_id,
    }


class PlannerLoopTests(unittest.TestCase):
    def _patched(self, executors=("R040",)):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch("aeris_runtime.engineering.planner.factory"))
        route_pod = stack.enter_context(patch("aeris_runtime.engineering.planner.route_pod"))
        route_pod.return_value = {"executors": list(executors)}
        run_role = stack.enter_context(patch("aeris_runtime.engineering.planner.run_role"))
        return route_pod, run_role

    def test_missing_required_input_stops_before_any_routing_or_execution(self):
        route_pod, run_role = self._patched()
        result = planner.plan_and_execute(
            "characterize array capture", available_params={},
            initial_skill_id="gcc-phat-tdoa", router=MagicMock())
        self.assertEqual(result["stop_reason"], "missing_required_input:gcc-phat-tdoa")
        route_pod.assert_not_called()
        run_role.assert_not_called()

    def test_step_failure_stops_immediately_without_a_decision_call(self):
        router = MagicMock()
        _, run_role = self._patched()
        run_role.return_value = _report("gcc-phat-tdoa", state="FAILED_EVIDENCE")
        result = planner.plan_and_execute(
            "x", available_params={"gcc-phat-tdoa": _TDOA_PARAMS},
            initial_skill_id="gcc-phat-tdoa", router=router)
        self.assertEqual(result["stop_reason"], "step_failed:FAILED_EVIDENCE")
        router.chat.assert_not_called()

    def test_chained_second_step_uses_models_decision_after_real_first_result(self):
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text=json.dumps({
            "decision": "CONTINUE", "next_skill_id": "delay-sum-beamforming",
            "reason": "confirmed geometry-consistent delay; validate beamforming gain",
        }))
        _, run_role = self._patched()
        run_role.side_effect = [
            _report("gcc-phat-tdoa", values={"delay_samples": 7, "tdoa_s": 7 / 48000}, run_id="RUN-1"),
            _report("delay-sum-beamforming", values={"rms": 0.7}, run_id="RUN-2"),
        ]
        result = planner.plan_and_execute(
            "characterize array capture",
            available_params={"gcc-phat-tdoa": _TDOA_PARAMS, "delay-sum-beamforming": _BEAMFORM_PARAMS},
            initial_skill_id="gcc-phat-tdoa", max_steps=2, router=router)
        self.assertEqual(
            [s["numerical_result"]["skill_id"] for s in result["steps"]],
            ["gcc-phat-tdoa", "delay-sum-beamforming"])
        self.assertEqual(result["stop_reason"], "max_steps_reached")
        # project_id from step 1's report threads into step 2's run_role call.
        self.assertEqual(run_role.call_args_list[1].kwargs["project_id"], "PROJECT-1")
        router.chat.assert_called_once()

    def test_repeated_skill_proposal_is_automatic_stop_not_retry(self):
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text=json.dumps({
            "decision": "CONTINUE", "next_skill_id": "gcc-phat-tdoa", "reason": "again",
        }))
        _, run_role = self._patched()
        run_role.return_value = _report("gcc-phat-tdoa", values={"delay_samples": 7})
        result = planner.plan_and_execute(
            "x", available_params={"gcc-phat-tdoa": _TDOA_PARAMS},
            initial_skill_id="gcc-phat-tdoa", max_steps=5, router=router)
        self.assertEqual(result["stop_reason"], "repeated_skill_no_progress")
        self.assertEqual(run_role.call_count, 1)

    def test_malformed_model_reply_stops_closed_without_raising(self):
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text="not json")
        _, run_role = self._patched()
        run_role.return_value = _report("gcc-phat-tdoa")
        result = planner.plan_and_execute(
            "x", available_params={"gcc-phat-tdoa": _TDOA_PARAMS},
            initial_skill_id="gcc-phat-tdoa", max_steps=5, router=router)
        self.assertEqual(result["stop_reason"], "planner_decision_invalid")

    def test_stop_decision_with_a_next_skill_id_is_rejected_as_malformed(self):
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text=json.dumps({
            "decision": "STOP", "next_skill_id": "gcc-phat-tdoa", "reason": "done",
        }))
        _, run_role = self._patched()
        run_role.return_value = _report("gcc-phat-tdoa")
        result = planner.plan_and_execute(
            "x", available_params={"gcc-phat-tdoa": _TDOA_PARAMS},
            initial_skill_id="gcc-phat-tdoa", max_steps=5, router=router)
        self.assertEqual(result["stop_reason"], "planner_decision_invalid")

    def test_risk_above_r1_rejected_before_any_call(self):
        router = MagicMock()
        with self.assertRaises(ValueError):
            planner.plan_and_execute("x", available_params={}, risk="R2", router=router)
        router.chat.assert_not_called()

    def test_max_steps_above_absolute_cap_rejected(self):
        with self.assertRaises(ValueError):
            planner.plan_and_execute("x", available_params={}, max_steps=9, router=MagicMock())

    def test_unknown_initial_skill_id_rejected(self):
        with self.assertRaises(ValueError):
            planner.plan_and_execute("x", available_params={}, initial_skill_id="not-a-real-skill", router=MagicMock())

    def test_falls_back_to_first_intake_proposed_skill_when_no_initial_skill_id(self):
        router = MagicMock()
        self._patched()
        with patch("aeris_runtime.engineering.planner.understand") as understand_mock:
            understand_mock.return_value = {"proposal": {"needed_skills": ["gcc-phat-tdoa", "spectral-analysis"]}}
            result = planner.plan_and_execute("x", available_params={}, router=router)
        understand_mock.assert_called_once()
        self.assertEqual(understand_mock.call_args.kwargs.get("router"), router)
        self.assertEqual(result["stop_reason"], "missing_required_input:gcc-phat-tdoa")


class PlannerEvidenceAndAuditTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        temp = ROOT / ".aeris/test-temp"
        temp.mkdir(parents=True, exist_ok=True)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(dir=temp)))
        self.stack.enter_context(patch.object(planner, "PLAN_EVIDENCE_DIR", root / "plans"))
        self.stack.enter_context(patch.object(audit, "AUDIT_FILE", root / "audit.jsonl"))

    def test_writes_plan_evidence_file_and_exactly_one_audit_event(self):
        router = MagicMock()
        with patch("aeris_runtime.engineering.planner.factory"), \
             patch("aeris_runtime.engineering.planner.route_pod", return_value={"executors": ["R040"]}), \
             patch("aeris_runtime.engineering.planner.run_role", return_value=_report("gcc-phat-tdoa", values={"delay_samples": 7})):
            result = planner.plan_and_execute(
                "x", available_params={"gcc-phat-tdoa": _TDOA_PARAMS},
                initial_skill_id="gcc-phat-tdoa", max_steps=1, router=router)

        plan_path = planner.PLAN_EVIDENCE_DIR / f"{result['plan_id']}.json"
        self.assertTrue(plan_path.is_file())
        record = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(record["plan_id"], result["plan_id"])
        self.assertEqual(record["stop_reason"], "max_steps_reached")

        events = [json.loads(line) for line in audit.AUDIT_FILE.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["event_type"] for e in events], ["PLAN_EXECUTED"])
        self.assertEqual(events[0]["payload"]["plan_id"], result["plan_id"])
        self.assertEqual(events[0]["payload"]["step_skill_ids"], ["gcc-phat-tdoa"])


if __name__ == "__main__":
    unittest.main()
