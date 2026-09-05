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

## Multi-capability Role Acceptance architecture checkpoint

The singular role-domain contract has been replaced by an ordered capability
list. Receipts and locators are now exact `(role, Skill)` records. Aggregate role
level is display/completeness truth only: every declared capability is required
for aggregate L2, while an intact A receipt remains executable/reviewable if a
new B is still missing. Reviewer routing, workflow execution, fixtures and all
eight company Challenges use exact Skill qualification. Each Challenge registry
entry now seals its executor Skill so adding B cannot make the scenario ambiguous.

Per-capability fingerprints bind exact implementation, Method, suite, Skill
assets and used shared predicates without coupling an unrelated handler. Ordered
contract-set transitions are retained in a local-only append-only SQLite ledger.
Each row has a separate sealed Evidence anchor outside that database. Concurrent
writers are serialized, and payload rewrite, trigger removal plus truncation,
missing anchor, or ledger/anchor reset beside an existing receipt fail closed.
SQLite, anchors and raw bundles remain under `.aeris` and are not published.

Independent plan review found two P1 design defects; independent Spec/Standards
reviews then found and reproduced six implementation edge cases. All were fixed,
their negative regressions pass, and both review axes report no open P0/P1/P2.
Final fixed-source regression: 378 PASS in 650.176 seconds, finished
2026-09-05T00:21:31.122624+00:00. Local transcript:
`.aeris/evidence/H0001-multi-capability-full-tests.log`, SHA-256
`10edb0cc3aceb93dfdef3ba162e463a98cb6311764da8da65bb190b1e402071e`.
Six real-browser semantic routes and all six dark/light exact-repeatability and
accessibility captures pass locally. Source coverage remains 67 executable
Skills/Methods, 25 role suites and 311 role cases; 75 roles still lack a domain
suite. This is prerequisite architecture, not P02/H0001 acceptance or L3/L4.
New Windows/Ubuntu CI is required on the pushed checkpoint.

## R011 ported-alignment construction checkpoint

R011 adds an ideal bounded Helmholtz port execution contract; R021 adds a second
exact reviewer qualification. The executor checks independent tuning bounds,
Q/S screening velocity, half-wave longitudinal-mode separation and compact
geometry. The independent reviewer recomputes the assertions through Decimal
arithmetic and rejects suppressed velocity or undeclared fields. Neither path
claims CFD/BEM, chuffing, waveguide directivity, calibration, L3/L4 or Human
approval.

Focused unit, Role Acceptance, capability-factory, reviewer-routing, sealed
Evidence and reproduction coverage passed 26 tests. Source inventory is now
69 executable Skills/Methods, 27 role suites and 319 role cases. Twenty-six
unique roles have at least one role-domain suite; 74 still lack one. Current
installed truth remains L1=100. H0001/P02 remains unfinished.

Fixed-source full regression: 382 PASS in 705.645 seconds. Private transcript
`.aeris/evidence/H0001-ported-full-tests.log`, SHA-256
`95de4cafd02e098b760f9a5c7ddcbab5d8cdd79e4daea3f2fa137fa613f1d16d`.

## R017 sampled speaker-polar construction checkpoint

R017 adds absolute horizontal polar coverage/sampling/reference/edge/symmetry
checks. R034 adds a second exact spatial reviewer capability with an independent
coordinate reconstruction. Thirty-five focused tests pass, including sealed
workflow review and reproduction plus sparse-grid, normalization, asymmetry and
R4 fail-closed cases. Source inventory is 71 executable Skills/Methods, 29 role
suites and 327 role cases; 27 unique roles have a suite and 73 still do not.
No continuous/full-sphere, calibration, L3/L4 or Human acceptance is claimed.

Fixed-source full regression: 386 PASS in 747.086 seconds. Private transcript
`.aeris/evidence/H0001-speaker-polar-full-tests.log`, SHA-256
`c7375c7af30ce64a2d4265b8ed04e917aa8540e1db7b0193944a4bc642709455`.
