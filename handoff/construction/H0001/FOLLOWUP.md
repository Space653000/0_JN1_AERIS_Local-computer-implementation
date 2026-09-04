# H0001 follow-up — work continues, not complete

## Shared/domain regression repair

The two failures recorded in the original SNAPSHOT were reproduced using
`python -B -m unittest tests.test_h0001_maturity -v` (one failure, one error).
The production factory intentionally separates shared Skill evidence from role
domain qualification. The old tests incorrectly used all required Skills as the
shared denominator and called the shared-only catalog on a domain Skill.

The corrected tests assert both total contract coverage and the smaller shared
evaluated count, require domain qualification to remain absent on the shared
path, and reject missing, duplicate and injected domain runs. Existing cross-seat,
stale-predicate, empty-check and missing-negative rejection tests remain.

Focused tests: 17 PASS in 19.498 seconds. Fixed-source full regression: 342 PASS
in 345.565 seconds, finished 2026-09-04T14:33:58.841747+00:00.
Local-only transcript: `.aeris/evidence/H0001-shared-domain-repair-full-tests.log`.
SHA-256: `67a89681c60869d301ad8340cb3bc5d698b3f3d226b1fab213f2b7942a6a4220`.

Discovery preceded the next standalone array-beam modules/tests, which are not
covered by this 342-test checkpoint. New Windows/Ubuntu CI must be checked on
the actual pushed follow-up commit. The original SNAPSHOT remains a historical
record; its failed test transcript is not overwritten. H0001 broader role depth,
live rollout and final acceptance are still unfinished. Do not merge or claim
P02 accepted.

## New CI visual-repeatability failure under investigation

CI run 199 on Ubuntu passed unit tests and browser semantics, then failed exact
same-route screenshot equality for Dashboard Dark. The same visual gate passed
locally on Windows. This is not yet diagnosed or fixed. Instrumentation now
preserves both failed images locally and reports only DOM element IDs and hashes
to distinguish asynchronous data/render changes. Exact screenshot equality is
unchanged; no retry discards a failed image. Two privacy-aware diagnostic tests
pass. Raw screenshots/runtime text are not uploaded by these changes.
