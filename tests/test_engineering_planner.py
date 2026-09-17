"""planner.plan_and_execute() is the first thing in the codebase that lets
step 2's skill choice depend on step 1's actual result. `run_role` is
mocked at the module's own import site (matching test_engineering_intake.py's
convention); `domain_skill_index()` is real, cheap (~10ms across all 100
roles) and deterministic, so skill-ID/required-input checks exercise the
genuine, currently-live domain-skill registry -- not a fake one that could
silently drift from reality.
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

# Real, currently-registered domain skills (each tied to exactly one role --
# see planner.py's module docstring for why this, not the shared catalog,
# is the only skill universe run_role() can actually execute). R075 is one
# of R016's real, curated professional_profiles.py neighbor_roles, so
# _SKILL_B is a genuinely offered candidate after _SKILL_A executes --
# unlike an arbitrary unrelated skill, which the neighbor-scoping fix
# (see planner.py's module docstring) would correctly never offer.
_SKILL_A = "speaker-power-distortion-baseline"  # R016
_SKILL_B = "speaker-thermal-domain-review"      # R075, a real neighbor of R016
_INDEX = planner.domain_skill_index()
_PARAMS_A = {field: 1.0 for field in _INDEX[_SKILL_A]["required_inputs"]}
_PARAMS_B = {field: {} for field in _INDEX[_SKILL_B]["required_inputs"]}


def _report(skill_id, state="EVIDENCED", values=None, project_id="PROJECT-1", run_id="RUN-1"):
    return {
        "project_id": project_id, "state": state,
        "numerical_result": {"skill_id": skill_id, "values": values or {}},
        "evidence_run_id": run_id,
    }


class PlannerLoopTests(unittest.TestCase):
    def _patched_run_role(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        return stack.enter_context(patch("aeris_runtime.engineering.planner.run_role"))

    def test_unknown_initial_skill_id_rejected_before_any_call(self):
        run_role = self._patched_run_role()
        with self.assertRaises(ValueError):
            planner.plan_and_execute("x", initial_skill_id="not-a-real-domain-skill",
                                      available_params={}, router=MagicMock())
        run_role.assert_not_called()

    def test_shared_catalog_skill_is_rejected_as_initial_skill_id(self):
        """gcc-phat-tdoa is a real skill, but a shared-catalog one --
        run_role() can never execute it (see module docstring), so it must
        never be accepted as a starting point either."""
        with self.assertRaises(ValueError):
            planner.plan_and_execute("x", initial_skill_id="gcc-phat-tdoa",
                                      available_params={}, router=MagicMock())

    def test_missing_required_input_stops_before_any_execution(self):
        run_role = self._patched_run_role()
        result = planner.plan_and_execute(
            "characterize power handling", available_params={},
            initial_skill_id=_SKILL_A, router=MagicMock())
        self.assertEqual(result["stop_reason"], f"missing_required_input:{_SKILL_A}")
        run_role.assert_not_called()

    def test_step_failure_stops_immediately_without_a_decision_call(self):
        router = MagicMock()
        run_role = self._patched_run_role()
        run_role.return_value = _report(_SKILL_A, state="FAILED_EVIDENCE")
        result = planner.plan_and_execute(
            "x", available_params={_SKILL_A: _PARAMS_A},
            initial_skill_id=_SKILL_A, router=router)
        self.assertEqual(result["stop_reason"], "step_failed:FAILED_EVIDENCE")
        router.chat.assert_not_called()

    def test_chained_second_step_uses_models_decision_after_real_first_result(self):
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text=json.dumps({
            "decision": "CONTINUE", "next_skill_id": _SKILL_B,
            "reason": "power handling nominal; check ANC topology margin next",
        }))
        run_role = self._patched_run_role()
        run_role.side_effect = [
            _report(_SKILL_A, values={"disposition": "BOUNDED_BASELINE_ACCEPT"}, run_id="RUN-1"),
            _report(_SKILL_B, values={"decision": "ACCEPT"}, run_id="RUN-2"),
        ]
        result = planner.plan_and_execute(
            "characterize this TWS design end to end",
            available_params={_SKILL_A: _PARAMS_A, _SKILL_B: _PARAMS_B},
            initial_skill_id=_SKILL_A, max_steps=2, router=router)
        self.assertEqual(
            [s["numerical_result"]["skill_id"] for s in result["steps"]], [_SKILL_A, _SKILL_B])
        self.assertEqual(result["stop_reason"], "max_steps_reached")
        # project_id from step 1's report threads into step 2's run_role call.
        self.assertEqual(run_role.call_args_list[1].kwargs["project_id"], "PROJECT-1")
        # the role actually executing step 2 is the skill's OWN owning role, R075 -- not R016.
        self.assertEqual(run_role.call_args_list[1].args[0], "R075")
        router.chat.assert_called_once()

    def test_repeated_skill_proposal_is_structurally_impossible_not_a_retry(self):
        """The just-executed skill is never in its own offered candidate
        set (candidates are built from neighbor_skill_ids with
        executed_skill_ids already excluded), so a model proposing it again
        is rejected the same way any not-offered skill would be -- there is
        no separate "already ran this" branch to bypass."""
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text=json.dumps({
            "decision": "CONTINUE", "next_skill_id": _SKILL_A, "reason": "again",
        }))
        run_role = self._patched_run_role()
        run_role.return_value = _report(_SKILL_A, values={"disposition": "BOUNDED_BASELINE_ACCEPT"})
        result = planner.plan_and_execute(
            "x", available_params={_SKILL_A: _PARAMS_A},
            initial_skill_id=_SKILL_A, max_steps=5, router=router)
        self.assertEqual(result["stop_reason"], "planner_decision_invalid")
        self.assertEqual(run_role.call_count, 1)

    def test_malformed_model_reply_stops_closed_without_raising(self):
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text="not json")
        run_role = self._patched_run_role()
        run_role.return_value = _report(_SKILL_A)
        result = planner.plan_and_execute(
            "x", available_params={_SKILL_A: _PARAMS_A},
            initial_skill_id=_SKILL_A, max_steps=5, router=router)
        self.assertEqual(result["stop_reason"], "planner_decision_invalid")

    def test_stop_decision_with_a_next_skill_id_is_rejected_as_malformed(self):
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text=json.dumps({
            "decision": "STOP", "next_skill_id": _SKILL_A, "reason": "done",
        }))
        run_role = self._patched_run_role()
        run_role.return_value = _report(_SKILL_A)
        result = planner.plan_and_execute(
            "x", available_params={_SKILL_A: _PARAMS_A},
            initial_skill_id=_SKILL_A, max_steps=5, router=router)
        self.assertEqual(result["stop_reason"], "planner_decision_invalid")

    def test_decision_proposing_a_non_neighbor_skill_is_rejected(self):
        """R005 owns real domain skills but is not one of R016's curated
        neighbor_roles -- a model proposal naming one of R005's skills must
        be rejected exactly like an unknown skill_id, not silently allowed
        just because it's a real skill somewhere in the registry."""
        non_neighbor_skill = "tws-anc-domain-review"  # R005, not a neighbor of R016
        router = MagicMock()
        router.chat.return_value = SimpleNamespace(text=json.dumps({
            "decision": "CONTINUE", "next_skill_id": non_neighbor_skill, "reason": "x",
        }))
        run_role = self._patched_run_role()
        run_role.return_value = _report(_SKILL_A, values={"disposition": "BOUNDED_BASELINE_ACCEPT"})
        result = planner.plan_and_execute(
            "x", available_params={_SKILL_A: _PARAMS_A},
            initial_skill_id=_SKILL_A, max_steps=5, router=router)
        self.assertEqual(result["stop_reason"], "planner_decision_invalid")

    def test_stops_with_no_neighbor_candidates_when_none_own_a_skill(self):
        """If the executing role's curated neighbors (or the role itself)
        aren't in the professional_profiles.py index -- or own no domain
        skill of their own -- the loop must stop cleanly rather than build
        an empty/malformed prompt."""
        router = MagicMock()
        run_role = self._patched_run_role()
        run_role.return_value = _report(_SKILL_A, values={"disposition": "BOUNDED_BASELINE_ACCEPT"})
        with patch("aeris_runtime.engineering.planner.role_profiles", return_value={}):
            result = planner.plan_and_execute(
                "x", available_params={_SKILL_A: _PARAMS_A},
                initial_skill_id=_SKILL_A, max_steps=5, router=router)
        self.assertEqual(result["stop_reason"], "no_neighbor_candidates:R016")
        router.chat.assert_not_called()

    def test_risk_above_r1_rejected_before_any_call(self):
        router = MagicMock()
        with self.assertRaises(ValueError):
            planner.plan_and_execute("x", initial_skill_id=_SKILL_A, available_params={}, risk="R2", router=router)
        router.chat.assert_not_called()

    def test_max_steps_above_absolute_cap_rejected(self):
        with self.assertRaises(ValueError):
            planner.plan_and_execute("x", initial_skill_id=_SKILL_A, available_params={}, max_steps=9, router=MagicMock())


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
        with patch("aeris_runtime.engineering.planner.run_role",
                   return_value=_report(_SKILL_A, values={"disposition": "BOUNDED_BASELINE_ACCEPT"})):
            result = planner.plan_and_execute(
                "x", available_params={_SKILL_A: _PARAMS_A},
                initial_skill_id=_SKILL_A, max_steps=1, router=router)

        plan_path = planner.PLAN_EVIDENCE_DIR / f"{result['plan_id']}.json"
        self.assertTrue(plan_path.is_file())
        record = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(record["plan_id"], result["plan_id"])
        self.assertEqual(record["stop_reason"], "max_steps_reached")

        events = [json.loads(line) for line in audit.AUDIT_FILE.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["event_type"] for e in events], ["PLAN_EXECUTED"])
        self.assertEqual(events[0]["payload"]["plan_id"], result["plan_id"])
        self.assertEqual(events[0]["payload"]["step_skill_ids"], [_SKILL_A])


if __name__ == "__main__":
    unittest.main()
