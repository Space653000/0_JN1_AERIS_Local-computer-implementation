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

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
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


def _evaluate_one(role_id: str) -> tuple[str, dict]:
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
    print(f"{role_id}: shared={entry['shared_skill']} domain={entry['domain']}", flush=True)
    return role_id, entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the capability factory pipeline for all canonical roles")
    parser.add_argument("--workers", type=int, default=8, help="parallel worker processes (roles are independent; measured ~1.7x faster than sequential on this machine, and clearly faster than threads -- the per-role work is dominated by hashing (pack/artifact/acceptance-engine/contract-set digests), which is CPU-bound and blocked by the GIL under threads)")
    parser.add_argument("--roles", nargs="*", help="only evaluate these role ids (default: all 100)")
    args = parser.parse_args()
    role_ids = args.roles if args.roles else [r["id"] for r in canonical_roles()]
    outcomes = {}
    # Each role's evaluation is independent (own files, own sealed Evidence
    # bundle with a unique run_id); the only shared resource is the audit
    # ledger's single-writer file lock (aeris_runtime/audit.py), which is an
    # OS-level file lock and therefore safe across separate processes too.
    # Processes, not threads: this workload is dominated by CPU-bound hashing
    # (see above), which the GIL serializes under threads -- measured threads
    # actually *slower* than sequential for this workload. No GPU-shaped work
    # exists here (no matrix/tensor math); this is a CPU-parallelism fix.
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(_evaluate_one, role_id): role_id for role_id in role_ids}
        for future in as_completed(futures):
            role_id, entry = future.result()
            outcomes[role_id] = entry

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
