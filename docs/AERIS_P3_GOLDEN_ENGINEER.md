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
**Status: done.** `_check_p3_1`-`_check_p3_4` added to
`aeris_runtime/progress_verify.py`. Deliberately read existing state (the
`.aeris/capability-factory/evaluations/` index, the live
`/api/v1/capabilities` snapshot) instead of re-running
`evaluate_role`/`RoleAcceptanceFactory` for all 100 roles on every check --
each of those calls seals a brand-new Evidence bundle, so re-running the full
pipeline on every `progress_verify` invocation would keep growing the
evidence store and re-trigger the exact telemetry slowdown found and fixed
earlier this session.

**New finding while wiring this up:** `/api/v1/capabilities` itself computes
its response synchronously over all 100 roles' evidence (unlike
`/api/v1/services`, which has the cached/async `TelemetryProjection`) and now
takes ~7s at the current evidence volume, up from whatever it was before this
session's 1000+ new sealed bundles. Not fixed this tick (would mean adding a
caching layer analogous to `TelemetryProjection`, a separate scoped change);
`progress_verify`'s HTTP timeout was raised from 5s to 30s to stop
misreporting a slow-but-working server as unreachable. The live
`capabilities.js` UI panel polls this endpoint every 10s, so at 7s it still
recovers each cycle rather than being permanently stuck like the telemetry
issue was -- but it is visibly laggier than before, and worth a dedicated
caching pass if the evidence store keeps growing (P5 territory).

## P3.6 — Push roles from L2 toward L3 (independent review)
**Requires:** L3 needs "independent role-specific domain acceptance with
independent decision oracle and qualified bounded review" -- a further step
past L2 that assigns a *different* role as reviewer and requires their
sign-off, per `aeris_runtime/engineering/reviewer_allocation.py` and the
R2-R4 risk-tier reviewer rules already tested in
`tests/test_reviewer_allocation.py`.
**Status: investigated, correctly not attempted this tick.** Unlike L2 (which
just needed someone to actually call already-built, already-tested functions
against already-present golden fixtures), `role_l3_accepted` is hardcoded
`False` everywhere it appears in `aeris_runtime/engineering/role_acceptance.py`
-- there is currently no code path anywhere in the repo that ever sets it
True. This is not a "press run" gap like P3.1-P3.4 were; it means the actual
L3 acceptance mechanism (what a qualified independent reviewer's sign-off
concretely is, how it gets sealed as Evidence, what makes a decision
"qualified") has not been designed yet, only named in the maturity rubric.
Building that now, under autonomous time pressure, risks inventing a
shortcut that *looks* like independent review without being one -- exactly
the "fake PASS" failure mode this whole Evidence system exists to prevent.
This needs a deliberate design pass (ideally with Human input on what
"qualified" review should require) before implementation, not a rushed
autonomous-loop tick.

## P3.7 — L4 remains explicitly out of reach by design
**Requires:** nothing to build. `verification_rubric["L4"]` in
`aeris_runtime/engineering/factory.py` already states L4 "cannot be granted
by this factory" -- it needs real instruments/calibration/expert approval.
**Status: correctly left alone.** No software change can honestly produce L4;
documenting that boundary is the entire acceptance criterion.

## P3.8 — Document the real, current numbers (not a projection)
**Requires:** whatever the actual run produces gets recorded as Evidence,
not rounded up or described optimistically.
**Status: done.** The real, current, live-verified numbers as of this
session's capability-factory run: **73/100 roles at L2 or higher**, **27/100
roles with no domain contract implemented yet** (disclosed via
`unresolved_capability_gaps`, not hidden), **0/100 at L3 or L4**. These are
not a projection or a target -- they are what `GET /api/v1/capabilities`
actually returns right now, and `aeris_runtime/progress_verify.py`'s P3.2/P3.3
checks re-verify these exact numbers (against a 70-role threshold and full
100-role accounting, respectively) every time it runs, so this document
cannot silently drift from reality.

## Sequencing this tick
P3.1-P3.4 (actually running the pipeline, handling multi-capability roles,
disclosing the no-contract roles honestly, as a repeatable script) are this
tick's slice. P3.5 (wire into progress_verify) and P3.6 (push toward L3) are
real next steps, each substantial enough to deserve its own tick rather than
being rushed onto the end of this one.
