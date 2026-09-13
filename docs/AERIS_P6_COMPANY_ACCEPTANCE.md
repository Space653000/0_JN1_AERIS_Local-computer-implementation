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

## P6.5 — Formal four-way release attestation is now wired
**Requires:** disclosing, rather than fabricating, whether the heavier
cryptographic four-way release-attestation mechanism
(`release_evidence.py:validate_version_tuple()`, which needs a pre-sealed
`version_tuple.json` and a signed implementer attestation) is actually
invoked by routine acceptance.
**Status: done -- mechanism fully built, wired, and tested; the Human's own
one-time key-generation step is the only remaining manual action, by
design.** The Human explicitly asked for this to be built now rather than
deferred. `release_evidence.py` already contained a complete, tested
two-party HMAC-signature verification engine (implementer attestation +
independent Human G5 approval, with subject/credential/context-collision
protection) from earlier work -- what was missing was production tooling
to actually use it and the wiring to call it instead of hardcoding
`False`. Both are now in place:

- `aeris_runtime/release_attestation.py`: computes the honest, objective
  version tuple (core/implementation SHAs, tracked-file digests for
  `config/` and `ui/web/`, and the real `SUPERVISOR_STARTED` audit-ledger
  timestamp -- refusing to fabricate any of it, e.g. it raises rather than
  guessing if the worktree is dirty or AERIS has never been started), seals
  an Evidence bundle for it, and signs AERIS's own **implementer**
  attestation with an auto-provisioned local key (`.aeris/authority/
  implementer.key`) that represents AERIS's own operating identity --
  never the Human's.
- `independent_acceptance()` (`review.py`) now calls
  `release_attestation.current_release_authority_status()` instead of
  hardcoding `False`; it reports `four_way_aligned: true` only once a real,
  independently-signed Human G5 receipt resolves against the current
  release, and otherwise reports the honest reason why not (e.g.
  `NO_RELEASE_AUTHORITY_TRUST_STORE_CONFIGURED`) as an informational
  `limits` entry, not a hard failure -- this remains an optional, heavier
  gate, not a routine-acceptance requirement.
- Three scripts give the Human a plain path to actually use it:
  `scripts/authority-keygen.py --human` (generates the Human's own key --
  deliberately not something AERIS can run on the Human's behalf, or the
  "independent" review would be fake), `scripts/prepare-release-
  attestation.py` (AERIS's half: version tuple + Evidence + implementer
  signature), and `scripts/mint-g5-approval.py` (the Human's half: signs
  the actual approval with their own key file).

**Why AERIS cannot complete this alone, even now:** `release_evidence.py`'s
own G5 gate check requires the reviewer principal to be `kind=='HUMAN'`
with `human_authority=='Human Chief Engineer'`, and separately rejects a
reviewer/implementer subject or key collision -- both enforced in code, not
just convention. Generating a "Human" key myself and signing with it would
technically satisfy every check while representing zero genuine independent
review, which is exactly the P3.6 "no automated process self-certifies
Human approval" principle this project has held everywhere else. Verified
end-to-end with a real (test) two-key signature exchange in
`tests/test_release_attestation.py`: 6/6 passing, including a dedicated
test that an implementer key can never resolve as its own reviewer.

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
write-up were new work. P6.5 needed a signing/attestation decision from the
Human before it could be wired -- the Human made that call explicitly
("現在就做" / do it now, reusing the existing HMAC two-party mechanism
rather than deferring or inventing a new scheme) -- and the mechanism is now
fully built, wired, and tested. All of P6.1-P6.8 are done. The one manual
step that remains, by design and forever (see P6.5 above), is the Human
running `authority-keygen.py`/`mint-g5-approval.py` themselves whenever they
want to formally bless a specific release -- that is not a gap, it is the
whole point of requiring an independent Human signature.
