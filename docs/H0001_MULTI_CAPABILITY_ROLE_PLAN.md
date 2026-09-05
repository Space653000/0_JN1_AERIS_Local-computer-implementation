# H0001 multi-capability Role Acceptance architecture plan

Fixed point: 7a3b6e85141474b3b527291d7a8407ed1edcc1de. Originating H0001
requirements: role-specific depth, separate Skill/Role acceptance, truthful
maturity and scalable Golden architecture. Core remains read-only; this changes
only Local Implementation. It is a prerequisite refactor, not a maturity award.

## Problem and invariant

Current `domain_execution_contract` is singular. `ROLE_DOMAIN_CONTRACTS` maps
one role to one Skill/suite, `RoleAcceptanceFactory` writes one role index, and
reviewer selection asks only for aggregate role status. Adding a second bounded
professional capability would overwrite or hide the first qualification. That
encourages one-token capability depth and cannot represent multiple independently
versioned/reviewed role questions.

Represent `domain_execution_contracts` as a nonempty ordered list. Each contract
must have a unique Skill ID and suite path inside that role's Golden directory.
The existing single-contract API remains an unambiguous convenience only when a
role has exactly one contract. A caller must name Skill ID when multiple exist.
No migration may turn an old single receipt into a current multi-capability pass.

## Source registry and packs

Change authored profile registry to `role -> [contract...]`. `enrich_pack()`
materializes the list, adds every Skill input/output mapping, and removes the
singular authority field. Contract validation verifies list type/nonempty when
present, unique Skills/suites, exact role/manifest/Method binding and contained
paths. Empty list means no domain capability, equivalent to absent.

Tracked packs are regenerated only from the authored role profile plus existing
pack contract; canonical role identity remains pinned/fail-closed. Do not copy
Core truth into a second mutable role identity source.

## Evidence and status

Store locators under `.aeris/role-acceptance/<role>/<skill>.json`, with strict
role and Skill identifier validation and root containment. Each locator points
to one sealed execution whose bindings include immutable role identity and the
exact Skill, Method, suite, implementation and contract hashes plus only shared
engine/policy hashes that can change that capability's verdict. It must not bind
the whole role pack or ordered contract set: adding or removing unrelated Skill
B must not stale an otherwise unchanged Skill A receipt. Changing A's contract,
implementation or a shared verdict predicate must stale A. Existing `<role>.json` locators are
legacy and ignored by the new engine after source/hash change; they cannot grant
qualification.

`evaluate(role, skill=None)` executes the named suite, writes only its locator,
then returns that capability status. `status_for_skill(role, skill)` validates
that exact receipt. `status(role)` aggregates every declared contract:

- L1 if no current bounded receipt or only a strict subset passes;
- L2 if every currently declared domain contract has current intact execution;
- never L3/L4 in this factory;
- include per-capability states and missing Skill IDs so partial depth is visible.

This aggregate is about declared implemented bounded capabilities, not complete
profession breadth. Always retain known-weakness text and role L3 gap. Adding a
new declared contract intentionally downgrades aggregate L2 to L1 until its own
suite passes without invalidating unchanged existing capability receipts. Track
an ordered contract-set digest separately for aggregate composition. Removing a
contract changes that digest and aggregate composition, and the history must
show that removal; it must not be used to preserve a number or silently rewrite
prior state, but it does not by itself stale surviving capability receipts.
Composition transitions are retained in a local-only SQLite append-only ledger
using serialized `BEGIN IMMEDIATE` writes and UPDATE/DELETE denial triggers.
Every ledger row has a separate sealed Evidence anchor outside that database;
the status reader verifies the row payload, chain, immutable role identity,
contract-set digest and every anchor. Missing ledger authority beside an
existing capability receipt, truncation, rewriting or anchor mismatch fails
closed rather than silently restarting at sequence one.

Capability implementation fingerprints are Skill-scoped. Dedicated executor
modules bind their explicitly imported verdict dependencies; review Skills bind
the exact review-domain AST branch, common predicates and declared delegated
modules. Current suites are replayed. Adding an unrelated handler or review
branch cannot stale A, while changing A or a shared predicate used by A does.

## Router, API and UI truth

Reviewer selection matches `review_domain` against each reviewer contract's
manifest, calls `status_for_skill`, and attaches that exact qualification run and
evidence ref. A role can review multiple domains, but executor/conflict exclusion
still applies to the whole role. One valid capability cannot qualify an adjacent
domain. Existing context/product/transducer/lifecycle/risk/evidence applicability
and independence rules remain.

Aggregate role level is presentation/completeness truth only. Execution and
review authorization must never use it. `run_role()` and every reviewer/router
path authorize the requested Skill through `status_for_skill(role, skill)`. Thus
an aggregate-L1 role may execute or review intact Skill A while incomplete Skill
B remains fail-closed.

Fixture API resolves exact `(role, skill)`; unknown or ambiguous requests fail.
Capability matrix exposes a `domain_capabilities` list, passed/declared counts,
and missing contracts. Total suites/cases remain actual files. Dashboard must not
compress partial multi-capability status into HEALTHY/L3.

## Compatibility and negative acceptance

Refactor existing 25 one-contract roles without changing case answers/counts.
All current focused and full tests must pass after updating singular field
assertions. Add deterministic tests:

1. a temporary two-contract pack where only one current receipt exists stays L1;
2. both intact exact receipts yield aggregate bounded L2;
3. missing/duplicate Skill or suite, cross-role suite, path escape and ambiguous
   no-Skill load/evaluate fail closed;
4. a receipt for Skill A cannot qualify review domain B;
5. tamper/reseal, stale source, deleted receipt and newly added contract downgrade;
6. fixture selection returns exact Skill suite and unknown Skill fails;
7. legacy singular locator cannot grant new status;
8. matrix reports declared/passed/missing values and preserves L3/L4 false.
9. aggregate L1 with valid Skill A still executes/reviews A, while missing Skill
   B is blocked;
10. adding B changes aggregate composition but leaves unchanged A current;
    changing A's contract/shared predicate stales A, and removing B cannot erase
    the recorded composition change or stale A without cause.
11. concurrent composition observation is serialized; DB trigger removal plus
    truncation, DB/anchor reset beside an existing receipt, payload rewrite and
    missing sealed anchors all fail closed.

Use isolated `.aeris/test-temp` SQLite/Evidence paths. Tests may construct
temporary pack/suite data only under that root or mock read-only source objects;
tracked production packs are never edited by tests. Keep raw Evidence local.

## Rollback and delivery

Implement as one source-compatible refactor before adding a role's second
capability. Run old single-contract tests first, then new multi-contract negative
tests, all unit tests, browser semantic/screenshot gates, secret/private scan and
Windows/Ubuntu PR CI. Commit/push only the H0001 branch; do not merge.

Rollback is the single refactor commit and its local Evidence locators. No live
supervisor replacement, maturity regeneration or company opening occurs in this
refactor. Completion means the source can truthfully retain two independent
capabilities on one role and all negative cases fail closed; it does not mean any
role is professionally complete or H0001/P02 accepted.
