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

## Array-domain and installer-dependency checkpoint

See `docs/H0001_ARRAY_BEAM_CHECKPOINT.md` and
`docs/H0001_DEPENDENCY_BOOTSTRAP.md` for implemented scope and known limits.
R034/R037 add 30 bounded role cases; source inventory is 23 suites / 280 cases,
65 engineering Skills/Methods. This is not whole-role L3 or H0001 completion.

Full local regression: 359 tests PASS in 377.014 seconds, completed
2026-09-04T15:01:32.306164+00:00. Private transcript
`.aeris/evidence/H0001-array-installer-full-tests.log`, SHA-256
`ada7ca00eeaf02cb6d1fd7ca8b2c0027ed91639220da132b8248df9462d0d360`.
That discovery preceded the additional PYTHONOPTIMIZE dependency-probe regression;
the final probe fix and all seven installer-helper tests separately pass. Do not
describe this 359-test transcript as covering the later-added regression.

An actual clean root-contained virtualenv rejected absent offline wheels, then
installed pinned free dependencies online and passed offline import. Private log
`.aeris/evidence/H0001-dependency-install-proof.log`, SHA-256
`f31b788345d381f73ca2b3e5fbf36cddb0e2571e39c418015a2e5581e8f6a420`.
That install proof preceded the optimization guard fix; the final helper was then
copied into the same isolated venv and passed offline with PYTHONOPTIMIZE=1.
No live venv replacement or full real-machine installer was performed.

Six local semantic browser routes and six exact-repeatability screenshots pass.
The running port-8765 six routes still return HTTP 200, but the old supervisor
has not been replaced and is not proof of current-source deployment.

CI run 200 localized the Ubuntu screenshot mismatch to identical DOM with
different PNGs, not demonstrated API-content divergence. The capture harness now
requests reduced motion and disables threaded animation/scrolling and the early
new-content rendering timeout; it also freezes the knowledge GET response. Exact
PNG equality remains mandatory. These render controls still require new Ubuntu
CI confirmation; a local Windows pass does not close that defect.

No Core/main/PR32 mutation, raw evidence, SQLite or binary upload is included.
Remaining 77 missing domain suites, broader product depth, external-source
knowledge and final clean-machine/live acceptance are still software work.

## Capture-clock depth and CI timeout follow-up

R032 now separates capture counter continuity, slot mapping, reference-relative
rate/timing intervals, channel alignment and callback delivery. R031 independently
reconstructs every counter and interval. Details and review dispositions are in
`docs/H0001_CAPTURE_CLOCK_PLAN.md`. The two roles add 31 cases; current source is
67 executable Skills/Methods, 25 role suites and 311 role cases. Seventy-five
roles still lack domain suites. No L3/L4 or absolute/physical clock claim is made.

Pre-compaction local regression: 371 PASS / 403.908 seconds; transcript SHA-256
`685be254f92dcb8fc0e4d89323e8e0b019704fa75dba5aa26b2f1b681cf13dea`.
Six browser semantics and six exact-repeatability screenshots PASS locally.
The finalized compact fixture engine and exact-path negative gate then completed
372 PASS / 396.918 seconds; local transcript SHA-256
`c9b8c9ee99f36629ebc2204851e8f56893427216185a4d7a14732c061773a9a9`.
Installed truth remains L1=100 because current source invalidates old receipts.

CI run 201 on ff9a7f5: Ubuntu completed SUCCESS, including screenshot, installer,
Autopilot, optional-wrapper and package gates. Windows passed unit, semantic,
screenshot, one-click installer and Autopilot, then was cancelled at the exact
35-minute job budget while the next retained wrapper test was running. No test
failure preceded cancellation. The matrix budget is now 50 minutes with a
regression that also requires every original acceptance path to remain present;
this change still needs the next Windows CI result.
