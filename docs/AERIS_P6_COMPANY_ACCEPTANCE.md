# P6 — Company Acceptance (concrete acceptance criteria)

Like P2/P4/P5 before it, `config/progress_truth.v1.json` reserves ids
P6.1-P6.8 with no written definition anywhere in the repo. The contract
file's own `allow_100_only_when` field is the one hint that already
existed: *"all required item scores are 100 and P6 comprehensive
acceptance is PASS"* -- P6 is the final, whole-company acceptance gate,
meant to be exercised once P0-P5 are substantially complete, not a phase
with independent feature work of its own.

## Where this phase actually lives in the codebase

Unlike P2/P4/P5, P6's mechanism was not missing -- it was built earlier in
this project's history and never named "P6":

- `aeris_runtime/review.py:independent_acceptance()` (the `aeris review`
  CLI command) is exactly a comprehensive company-acceptance check: it
  validates the company manifest, Core cache integrity, audit ledger
  integrity, a clean versioned worktree, deterministic test results, remote
  Core drift, machine-profile support, real-machine acceptance evidence,
  company opening state, supervisor reachability, unattended
  install/runtime persistence, and expected-run health -- then reduces all
  of that to a fail-closed `FAIL` / `BLOCKED` / `PASS_WITH_LIMITS` / `PASS`
  ladder, never a silent `PASS`.
- `aeris_runtime/completion.py:assess()` (the `python -m
  aeris_runtime.completion` entrypoint) is a second, complementary
  comprehensive check: every `SOFTWARE_LOCAL_FIXABLE` item in
  `.aeris/state/COMPANY_COMPLETION_PASS.json` is re-validated against a
  real executable check (`CHECKS`/`GATE_CHECKS`), not a tracked label.

## P6.1 — A real, executable independent-acceptance mechanism exists
**Requires:** the "P6 comprehensive acceptance" the contract file already
names must be a real, callable, fail-closed check, not aspirational.
**Status: done, pre-existing.** `independent_acceptance()` is exactly this;
it has been callable via `aeris review` since before this phase was named.

## P6.2 — Comprehensive completion assessment re-validates, not tracks
**Requires:** completion status comes from re-running real checks against
current state, the same "never trust a tracked label" principle as P2.2's
progress engine and P3's role acceptance.
**Status: done, pre-existing.** `completion.assess()`'s own `truth` field
says this explicitly: *"Completion is derived from executable evidence
checks plus the maturity scan; tracked COMPLETE labels are not trusted as
proof."*

## P6.3 — Company acceptance is fail-closed on audit/Core integrity
**Requires:** the final acceptance gate must fail (not merely warn) if the
audit ledger or Core cache is invalid.
**Status: done, pre-existing.** `independent_acceptance()` appends
`AUDIT_LEDGER_INVALID` / `CORE_CACHE_INTEGRITY_FAIL` to `failures` (which
forces `final_result = FAIL`) whenever `verify_ledger()` or
`verify_core_cache()` reports invalid.

## P6.4 — Company acceptance is fail-closed on a dirty/unclean worktree
**Requires:** a versioned implementation with uncommitted changes cannot
pass final acceptance.
**Status: done, pre-existing.** `_versioned_worktree_dirty()` feeding
`VERSIONED_IMPLEMENTATION_WORKTREE_DIRTY` into `failures`.

## P6.5 — Formal four-way release attestation is honestly not yet wired
**Requires:** disclosing, rather than fabricating, whether the heavier
cryptographic four-way release-attestation mechanism
(`release_evidence.py:validate_version_tuple()`, which needs a pre-sealed
`version_tuple.json` and a signed implementer attestation) is actually
invoked by routine acceptance.
**Status: genuine, disclosed gap.** `independent_acceptance()` hardcodes
`four_way_aligned: False` rather than calling `validate_version_tuple()` --
correctly, since that function expects signing/attestation infrastructure
this local company does not have configured. This is not a "forgot to
wire it" gap like P2/P4/P5's; it is a deliberately heavier, formal-release-
only mechanism this local-first company has not been asked to stand up.
Left honestly `False` rather than faked `True`.

## P6.6 — Company acceptance requires real-machine evidence, not just tests
**Requires:** unit tests passing alone must not be sufficient; there must be
a real, current, this-machine acceptance record.
**Status: done, pre-existing.** `independent_acceptance()` reads
`REAL_MACHINE_ACCEPTANCE_NOT_PRESENT` / `REAL_MACHINE_ACCEPTANCE_FAILED`
from `.aeris/state/LOCAL_ACCEPTANCE.json`, produced by
`scripts/local-acceptance.ps1`/`.sh`, separately from unit tests.

## P6.7 — P6 is gated behind P0-P5, not run in isolation
**Requires:** per the contract file's own `allow_100_only_when`, this phase
is the final gate exercised once everything else is substantially done, not
an independent feature backlog with its own P6.1-P6.8 UI or dashboard.
**Status: acknowledged.** No new UI surface was built for "P6 progress";
its two real entrypoints (`aeris review`, `python -m
aeris_runtime.completion`) already existed and are exercised directly, the
same way `aeris_runtime core verify` is exercised directly rather than
through a dedicated progress-phase UI.

## P6.8 — Wire P6.1-P6.4/P6.6 into `aeris_runtime.progress_verify`
**Requires:** the same reproducible-check treatment every other phase's
items got, not a one-off manual claim.
**Status: this session's target**, alongside this document. See
`aeris_runtime/progress_verify.py`'s `_check_p6_*` functions.

## Sequencing
P6.1-P6.4/P6.6/P6.7 describe mechanisms that already existed before this
document was written; only the `progress_verify` wiring (P6.8) and this
write-up were new work. P6.5 stays an honestly disclosed gap: it needs a
signing/attestation decision from the Human before it could ever be wired,
not a code change this session can make unilaterally.
