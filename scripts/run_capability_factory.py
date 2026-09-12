"""P3 Golden Engineer: actually execute the already-built capability-factory
pipeline (aeris_runtime.engineering.factory.evaluate_role +
aeris_runtime.engineering.role_acceptance.RoleAcceptanceFactory) for every
canonical role, instead of leaving it built but never run.

This does not invent new engineering capability -- it exercises existing,
tested code against existing golden fixtures/contracts and reports the real,
current outcome per role, including roles that cannot yet reach L2 because
their role-specific execution contract has not been implemented (an honest
gap, not a bug in this script).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aeris_runtime.engineering.factory import evaluate_role, canonical_roles, load_pack, domain_contracts
from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory


def _evaluate_domain(role_id: str) -> dict:
    """Multi-capability roles need an explicit skill_id; try each of the
    role's domain contracts and report the best outcome, not just the first."""
    try:
        return RoleAcceptanceFactory().evaluate(role_id)
    except ValueError as exc:
        if "explicit Skill ID required" not in str(exc):
            raise
    pack = load_pack(role_id)
    contracts = domain_contracts(pack) or []
    attempts = {}
    for contract in contracts:
        skill_id = contract["skill_id"]
        try:
            attempts[skill_id] = RoleAcceptanceFactory().evaluate(role_id, skill_id)
        except Exception as exc:
            attempts[skill_id] = {"error": f"{type(exc).__name__}: {exc}"}
    passed = [r for r in attempts.values() if isinstance(r, dict) and r.get("execution_passed")]
    best = passed[0] if passed else next(iter(attempts.values()))
    return {**best, "all_skill_attempts": attempts}


def main() -> int:
    role_ids = [r["id"] for r in canonical_roles()]
    outcomes = {}
    for role_id in role_ids:
        entry = {"shared_skill": None, "domain": None}
        try:
            shared = evaluate_role(role_id)
            entry["shared_skill"] = {"all_executable": shared["all_executable"], "all_evaluated": shared["all_evaluated"]}
        except Exception as exc:
            entry["shared_skill"] = {"error": f"{type(exc).__name__}: {exc}"}
        try:
            domain = _evaluate_domain(role_id)
            entry["domain"] = {"level": domain["level"], "execution_passed": domain["execution_passed"], "reason": domain.get("reason")}
        except Exception as exc:
            entry["domain"] = {"error": f"{type(exc).__name__}: {exc}"}
        outcomes[role_id] = entry
        print(f"{role_id}: shared={entry['shared_skill']} domain={entry['domain']}", flush=True)

    l2_or_higher = [rid for rid, e in outcomes.items() if isinstance(e["domain"], dict) and e["domain"].get("level") in {"L2", "L3", "L4"}]
    no_contract = [rid for rid, e in outcomes.items() if isinstance(e["domain"], dict) and "not yet implemented" in str(e["domain"].get("error", ""))]
    other_errors = [rid for rid, e in outcomes.items() if isinstance(e["domain"], dict) and e["domain"].get("error") and rid not in no_contract]

    summary = {
        "total_roles": len(role_ids),
        "reached_l2_or_higher": len(l2_or_higher),
        "l2_or_higher_role_ids": l2_or_higher,
        "no_domain_contract_implemented": len(no_contract),
        "other_errors": {rid: outcomes[rid]["domain"]["error"] for rid in other_errors},
    }
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
