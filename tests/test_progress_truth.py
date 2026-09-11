import copy
import json
import tempfile
import unittest
from pathlib import Path

import aeris_runtime.progress as progress
from aeris_runtime.progress_truth import CANONICAL_AUTHORITY_SHA, evaluate_progress


ROOT = Path(__file__).resolve().parents[1]


def record(item, result="PASS", score=100):
    return {
        "authority_sha": CANONICAL_AUTHORITY_SHA,
        "source_sha": "7d5368b83b07f776a800836416f2f39ce45a1ef3",
        "evidence_type": "local_acceptance",
        "evidence_pointer": f".aeris/evidence/progress/{item}.json",
        "acceptance_gate": item,
        "result": result,
        "score": score,
        "observed_at": "2026-09-11T09:30:50Z",
        "blocker": None,
        "next_action": "建立下一項 authoritative Evidence",
    }


class ProgressTruthTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / "config" / "progress_truth.v1.json").read_text(encoding="utf-8"))
        self.ids = [item for phase in self.contract["required_items"].values() for item in phase]

    def test_contract_has_exactly_54_unique_items_and_required_provenance(self):
        self.assertEqual(len(self.ids), 54)
        self.assertEqual(len(set(self.ids)), 54)
        self.assertEqual(set(self.contract["provenance_required_fields"]), {
            "authority_sha", "source_sha", "evidence_type", "evidence_pointer", "result", "observed_at",
        })

    def test_missing_evidence_is_unknown_and_cannot_add_progress(self):
        result = evaluate_progress(self.contract, {"items": {}})
        self.assertEqual(result.state, "UNKNOWN")
        self.assertEqual(result.overall_percent, 0)
        self.assertEqual(result.item_scores["P0.6"], None)

    def test_wrong_authority_or_result_score_conflict_fails_closed(self):
        observations = {"items": {item: record(item) for item in self.ids}}
        broken = copy.deepcopy(observations)
        broken["items"]["P0.6"]["authority_sha"] = "0" * 40
        self.assertEqual(evaluate_progress(self.contract, broken).state, "FAIL_CLOSED")
        broken = copy.deepcopy(observations)
        broken["items"]["P0.6"].update(result="PASS", score=80)
        self.assertIn("result_score_conflict:P0.6", evaluate_progress(self.contract, broken).errors)

    def test_100_requires_separate_p6_acceptance(self):
        observations = {"items": {item: record(item) for item in self.ids}}
        self.assertEqual(evaluate_progress(self.contract, observations).state, "FAIL_CLOSED")
        observations["p6_comprehensive_acceptance"] = "PASS"
        self.assertEqual(evaluate_progress(self.contract, observations).state, "VALID")

    def test_observation_requires_gate_blocker_and_next_action_fields(self):
        observations = {"items": {"P0.6": record("P0.6")}}
        del observations["items"]["P0.6"]["acceptance_gate"]
        self.assertEqual(evaluate_progress(self.contract, observations).item_scores["P0.6"], None)

    def test_runtime_projection_fails_closed_when_runtime_is_not_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "progress_truth.v1.json").write_text(json.dumps(self.contract), encoding="utf-8")
            evidence = root / ".aeris" / "evidence" / "progress"
            evidence.mkdir(parents=True)
            pointer = evidence / "P0.6.json"
            pointer.write_text('{"real": true}', encoding="utf-8")
            observation = record("P0.6") | {
                "evidence_pointer": ".aeris/evidence/progress/P0.6.json",
                "acceptance_gate": "P0.6",
                "blocker": None,
                "next_action": "P0.7",
            }
            (evidence / "PROGRESS_TRUTH.json").write_text(json.dumps({"items": {"P0.6": observation}}), encoding="utf-8")
            old_root = progress.ROOT
            old_status = progress.supervisor_status
            old_head = progress._head_sha
            try:
                progress.ROOT = root
                progress.supervisor_status = lambda: {"reachable": True, "implementation_sha": observation["source_sha"]}
                progress._head_sha = lambda: "different-candidate"
                payload = progress.current()
            finally:
                progress.ROOT = old_root
                progress.supervisor_status = old_status
                progress._head_sha = old_head
            self.assertEqual(payload["truth_state"], "FAIL_CLOSED")
            self.assertIsNone(payload["overall_percent"])
            self.assertIn("runtime_candidate_mismatch", payload["truth_errors"])

    def test_runtime_projection_uses_existing_evidence_with_matching_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "progress_truth.v1.json").write_text(json.dumps(self.contract), encoding="utf-8")
            evidence = root / ".aeris" / "evidence" / "progress"
            evidence.mkdir(parents=True)
            pointer = evidence / "P0.6.json"
            pointer.write_text('{"real": true}', encoding="utf-8")
            observation = record("P0.6") | {
                "evidence_pointer": ".aeris/evidence/progress/P0.6.json",
                "acceptance_gate": "P0.6",
                "blocker": None,
                "next_action": "P0.7",
            }
            (evidence / "PROGRESS_TRUTH.json").write_text(json.dumps({"items": {"P0.6": observation}}), encoding="utf-8")
            old_root = progress.ROOT
            old_status = progress.supervisor_status
            old_head = progress._head_sha
            try:
                progress.ROOT = root
                progress.supervisor_status = lambda: {"reachable": True, "implementation_sha": observation["source_sha"]}
                progress._head_sha = lambda: observation["source_sha"]
                payload = progress.current()
            finally:
                progress.ROOT = old_root
                progress.supervisor_status = old_status
                progress._head_sha = old_head
            item = next(item for item in payload["items"] if item["id"] == "P0.6")
            self.assertEqual(payload["truth_state"], "UNKNOWN")
            self.assertEqual(payload["phase_percent"]["P0"], 14)
            self.assertEqual(item["state"], "PASS")
            self.assertEqual(item["evidence"], observation["evidence_pointer"])


if __name__ == "__main__":
    unittest.main()
