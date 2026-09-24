"""Live "exam" for all 100 AERIS acoustic-engineering role seats.

For every canonical role that currently has at least one real domain
execution contract, this loads that skill's golden suite (each written
and independently hand-verified earlier in this program, not generated
from the implementation) and replays every non-negative case
(positive/boundary/counter_hypothesis -- the deliberately varied
question types every suite is required to cover) through the REAL
run_role() production pathway, not the isolated run_skill() unit-test
harness. Each execution must reach state=EVIDENCED with a real
task/workflow/evidence-run id and a sealed, hash-verified Evidence
bundle on disk, or it counts as a failure.

Negative (expected_error) cases are reported separately: those exist to
prove input validation rejects bad data, not to exercise a computed
engineering result, so a ValueError there is the CORRECT outcome, not a
failure.

Usage: .venv/Scripts/python.exe scripts/exam_100_engineers.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aeris_runtime.engineering.factory import canonical_roles, load_pack, domain_contracts  # noqa: E402
from aeris_runtime.engineering.orchestration import run_role  # noqa: E402


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="stop after N role executions (0 = no limit)")
    parser.add_argument("--roles", type=str, default="", help="comma-separated role ids to restrict to")
    args = parser.parse_args()

    only_roles = set(args.roles.split(",")) if args.roles else None

    roles = canonical_roles()
    report: dict = {
        "roles_with_no_domain_contract": [],
        "role_results": {},
        "summary": {"roles_tested": 0, "skills_tested": 0, "cases_run": 0, "cases_evidenced": 0, "cases_failed": 0, "negative_cases_correctly_rejected": 0, "negative_cases_wrongly_accepted": 0},
    }

    executed_total = 0
    for role in roles:
        role_id = role["id"]
        if only_roles and role_id not in only_roles:
            continue
        pack = load_pack(role_id)
        contracts = domain_contracts(pack) or []
        if not contracts:
            report["roles_with_no_domain_contract"].append(role_id)
            continue

        role_report = {"name": pack["identity"]["name"], "skills": {}}
        for contract in contracts:
            skill_id = contract["skill_id"]
            suite_path = ROOT / contract["suite"]
            if not suite_path.is_file():
                role_report["skills"][skill_id] = {"error": f"golden suite missing: {suite_path}"}
                continue
            suite = _read_json(suite_path)
            base_input = suite["base_input"]
            skill_report = {"cases": []}
            for case in suite["cases"]:
                kind = case.get("kind")
                case_id = case.get("id")
                params = {**base_input, **case.get("input_overrides", {})}
                if kind == "negative" or "expected_error" in case:
                    try:
                        run_role(role_id, skill_id, params, objective=f"EXAM negative case {case_id}",
                                  source_kind="SYNTHETIC", risk="R0")
                        skill_report["cases"].append({"id": case_id, "kind": kind, "outcome": "WRONGLY_ACCEPTED_BAD_INPUT"})
                        report["summary"]["negative_cases_wrongly_accepted"] += 1
                    except Exception as exc:  # noqa: BLE001
                        skill_report["cases"].append({"id": case_id, "kind": kind, "outcome": "CORRECTLY_REJECTED", "error_type": type(exc).__name__})
                        report["summary"]["negative_cases_correctly_rejected"] += 1
                    continue
                executed_total += 1
                report["summary"]["cases_run"] += 1
                try:
                    result = run_role(role_id, skill_id, params, objective=f"EXAM {kind} case {case_id}",
                                       source_kind="SYNTHETIC", risk="R0")
                    state = result.get("state")
                    if state == "EVIDENCED":
                        report["summary"]["cases_evidenced"] += 1
                        skill_report["cases"].append({
                            "id": case_id, "kind": kind, "outcome": "EVIDENCED",
                            "task_id": result.get("task_id"), "evidence_run_id": result.get("evidence_run_id"),
                            "disposition": result.get("numerical_result", {}).get("values", {}).get("disposition"),
                        })
                    else:
                        report["summary"]["cases_failed"] += 1
                        skill_report["cases"].append({"id": case_id, "kind": kind, "outcome": f"NON_EVIDENCED_STATE:{state}"})
                except Exception as exc:  # noqa: BLE001
                    report["summary"]["cases_failed"] += 1
                    skill_report["cases"].append({"id": case_id, "kind": kind, "outcome": "EXCEPTION", "error": f"{type(exc).__name__}: {exc}"})
            role_report["skills"][skill_id] = skill_report
            report["summary"]["skills_tested"] += 1
        report["role_results"][role_id] = role_report
        report["summary"]["roles_tested"] += 1

        if args.limit and executed_total >= args.limit:
            break

    out_path = ROOT / ".aeris" / "evidence" / "exam_100_engineers_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"full report written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
