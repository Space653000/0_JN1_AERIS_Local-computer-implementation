"""Diagnostic: measure per-role wall-clock time for the same status
computation /api/v1/capabilities performs across all 100 roles, to find
whether a slowdown is fixed-per-role overhead or scales with a specific
role's accumulated Evidence. See .claude/skills/aeris-gate/SKILL.md's
"Known performance traps" section for the 2026-09-13 baseline
measurement (~70s total, ~0.5-2s/role, not evidence-store-size-scaling)."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aeris_runtime.engineering import factory
from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
from aeris_runtime.engineering.professional_profiles import profiles

role_factory = RoleAcceptanceFactory()
roles = factory.canonical_roles()
profile_registry = profiles()
definition_registry = factory.catalog.definitions()

per_role = []
t0 = time.perf_counter()
for role in roles:
    rt0 = time.perf_counter()
    try:
        pack = factory.load_pack(role["id"])
        errors = factory.contract_errors(pack, profile_registry=profile_registry, definition_registry=definition_registry)
        if not errors and factory.domain_contracts(pack):
            role_factory.status(role["id"], pack=pack, errors=errors)
    except Exception as exc:
        print(role["id"], "ERROR", exc)
    per_role.append((role["id"], time.perf_counter() - rt0))
total = time.perf_counter() - t0

per_role.sort(key=lambda x: -x[1])
print(f"TOTAL: {total:.2f}s across {len(roles)} roles")
print("Top 10 slowest roles:")
for role_id, dt in per_role[:10]:
    print(f"  {role_id}: {dt:.3f}s")
