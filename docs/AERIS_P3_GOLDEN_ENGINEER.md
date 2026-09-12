# P3 — Golden Engineer (concrete acceptance criteria)

Like P1/P2 before it, `config/progress_truth.v1.json` reserves ids P3.1-P3.8
with no written definition anywhere in the repo. This document defines them,
grounded in what was actually found when this phase was investigated: a
substantial, already-built, already-tested capability-execution pipeline
(`aeris_runtime.engineering.factory.evaluate_role` +
`aeris_runtime.engineering.role_acceptance.RoleAcceptanceFactory`, with golden
fixtures already present for 73 of the 100 roles under `golden/roles/`) that
had simply never been *run* for any role — nothing in the codebase called it.
`docs/AERIS_BUILD_PHASES.md` Phase 02 names `100_role_L2 = 100/100` as its
primary stop condition; P3 is that work.

## What "Golden Engineer" means here

Not writing new acoustic engineering logic from scratch. It means actually
exercising the existing execute -> evidence -> independent-review pipeline for
real roles against their real golden fixtures, so maturity levels (L0-L4)
reflect roles that have genuinely been run, not just roles with a registered
contract sitting unused.

## P3.1 — Run the shared-skill evaluation pipeline for every role
**Requires:** `aeris_runtime.engineering.factory.evaluate_role(role_id)` is
actually invoked for all 100 canonical roles, sealing real Evidence bundles.
**Status: done this session.** `scripts/run_capability_factory.py` calls it
for all 100 roles.

## P3.2 — Run role-specific domain acceptance for every role that has a contract
**Requires:** `RoleAcceptanceFactory().evaluate(role_id, skill_id)` run for
every role with an implemented domain contract (single- or multi-capability),
correctly handling roles that expose more than one domain contract.
**Status: done this session**, including the multi-capability-role fix
(`_evaluate_domain` in the script tries every contract's skill_id rather than
failing on "explicit Skill ID required").

## P3.3 — Honest accounting of roles that cannot reach L2 yet
**Requires:** roles with no implemented domain contract report that plainly
(not silently treated as failures indistinguishable from a real regression).
**Status: done.** The script's summary separates `no_domain_contract_implemented`
from `other_errors`; as of this session's run, 27 roles (mostly governance/
chief-architect seats like R001) have no domain contract yet -- a real,
disclosed gap, not something this session invented a fake contract to hide.

## P3.4 — Wire this into the acceptance/CI-adjacent path
**Requires:** the capability factory run is repeatable via a checked-in
script (not a one-off interactive Python session), so a future session can
re-run it after adding a new role's domain contract.
**Status: done.** `scripts/run_capability_factory.py` is a real, argument-free,
idempotent entrypoint.

## P3.5 — Extend `aeris_runtime.progress_verify` to cover this
**Requires:** the P2 Progress Engine can check "how many roles are L2+" the
same reproducible way it checks P0/P1 items, instead of this being a manual
one-off script run.
**Status: gap, next increment.** Natural follow-up once P3.1-P3.4 are proven;
not done this tick to keep this session's change reviewable.

## P3.6 — Push roles from L2 toward L3 (independent review)
**Requires:** L3 needs "independent role-specific domain acceptance with
independent decision oracle and qualified bounded review" -- a further step
past L2 that assigns a *different* role as reviewer and requires their
sign-off, per `aeris_runtime/engineering/reviewer_allocation.py` and the
R2-R4 risk-tier reviewer rules already tested in
`tests/test_reviewer_allocation.py`.
**Status: not attempted this tick.** This is real, larger work (running an
actual independent-review pass across dozens of roles) better scoped as its
own increment once L2 coverage is stable.

## P3.7 — L4 remains explicitly out of reach by design
**Requires:** nothing to build. `verification_rubric["L4"]` in
`aeris_runtime/engineering/factory.py` already states L4 "cannot be granted
by this factory" -- it needs real instruments/calibration/expert approval.
**Status: correctly left alone.** No software change can honestly produce L4;
documenting that boundary is the entire acceptance criterion.

## P3.8 — Document the real, current numbers (not a projection)
**Requires:** whatever the actual run produces gets recorded as Evidence,
not rounded up or described optimistically.
**Status: this document + the Evidence written after the batch run in this
session.**

## Sequencing this tick
P3.1-P3.4 (actually running the pipeline, handling multi-capability roles,
disclosing the no-contract roles honestly, as a repeatable script) are this
tick's slice. P3.5 (wire into progress_verify) and P3.6 (push toward L3) are
real next steps, each substantial enough to deserve its own tick rather than
being rushed onto the end of this one.
