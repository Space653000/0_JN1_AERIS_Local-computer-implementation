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

## R018 sampled tonal / R020 context-review construction checkpoint

R018 adds an absolute level-matched sampled tonal correction contract with
explicit spatial uncertainty, smoothing, unresolved-resonance, boost/cut,
headroom, deep room-notch and loudness-match gates. R020 independently
reconstructs the complete candidate and rejects hidden headroom or outside-scope
R4 use. Exact capability routing, review Evidence and reproduction pass. No
realized filter, audibility, preference, calibration, L3/L4 or Human acceptance
is claimed.

Focused regression: 26 PASS. Fixed-source regression: 390 PASS in 732.098
seconds. Six semantic browser routes and six fixed-environment dark/light
screenshot repeatability/basic-accessibility routes pass. Source inventory is
73 executable Skills/Methods, 31 role suites and 335 role cases; 29 unique
roles have a suite and 71 still do not. Installed truth remains L1=100, so
H0001/P02 remains unfinished.

Private transcript `.aeris/evidence/H0001-tonal-full-tests.log`, SHA-256
`a407aab318c2814c02cea7e38ef3b4bcb6e6e6ecb62d8e5e8aeedfbfa171fb4b`.

## Speaker signal-chain / protection / structural-path checkpoint

R012/R013 add exact gain-chain noise/loading/headroom execution and independent
review. R019/R025 add bass-boost excursion/thermal/limiter-envelope execution
and independent protection review. R022/R073 add synchronized structural/
acoustic transfer identifiability and a reviewer that rejects causal overclaim.
Each pair has positive, inclusive-boundary, negative, counter-hypothesis, exact
reviewer routing, sealed Evidence and reproduction coverage. None claims bench,
calibration, listener, durability, causality, L3/L4 or Human acceptance.

Focused regression: 34 PASS. Fixed-source regression: 402 PASS in 918.149
seconds. Six semantic routes and six dark/light fixed-environment screenshot/
basic-accessibility routes pass. Inventory: 79 Skills, 79 Methods, 37 role
suites, 359 cases, 35 roles with a suite and 65 without one. Installed truth is
still L1=100 and H0001/P02 remains unfinished.

Private transcript `.aeris/evidence/H0001-speaker-depth-full-tests.log`, SHA-256
`07536fe7c5c92a894df7b821a4d0ed6fa1d6eddb9ee11787857213318efe258d`.

## Room decay / correction spatial checkpoint

R023/R072 add multi-position decay execution and independent spatial review.
R026/R071 add bounded sampled room-correction execution and independent review.
Positive, boundary, negative, counter-hypothesis, exact reviewer routing,
sealed Evidence and reproduction coverage pass. These contracts do not claim a
diffuse field, complete room model, realized filter, audibility, calibration,
physical measurement, L3/L4 or Human acceptance.

Focused regression: 30 PASS. Fixed-source regression: 410 PASS in 1011.760
seconds. Six semantic routes and six dark/light fixed-environment screenshot/
basic-accessibility routes pass. Inventory: 83 Skills, 83 Methods, 41 role
suites, 375 cases, 39 roles with a suite and 61 without one. Installed truth is
still L1=100 and H0001/P02 remains unfinished.

Private transcript `.aeris/evidence/H0001-room-depth-full-tests.log`, SHA-256
`bb2ae2065c119ee1f4c4514bd0749714881db8a2bb5baf8a8fecb522ac2e88aa`.

## Speaker digital transport / filter realization checkpoint

R014/R032 add declared I2S/TDM format, clock, slot-map and service-buffer
execution plus independent review. R024/R005 add declared biquad stability,
quantization, crossover, headroom and delay execution plus independent review.
Exact multi-capability Skill selection, sealed Evidence, reviewer routing and
reproduction pass. No electrical timing, driver execution, full-band
fixed-point behavior, physical playback, L3/L4 or Human acceptance is claimed.

Focused regression and affected exact-Skill regression: 30 PASS each.
Fixed-source regression: 418 PASS in 1091.297 seconds. Six semantic routes and
six dark/light fixed-environment screenshot/basic-accessibility routes pass;
the first cold visual capture failed closed on pending telemetry and the
unchanged gate passed after collection completed. Inventory: 87 Skills, 87
Methods, 45 role suites, 391 cases, 41 roles with a suite and 59 without one.
Speaker CoE is 18/18; Microphone CoE remains 10/18. Installed truth is still
L1=100 and H0001/P02 remains unfinished.

Private transcript `.aeris/evidence/H0001-speaker-completion-full-tests.log`,
SHA-256 `5d5fa635b478bffeb546bded9f533de016bcfe63c4303f1c7ab7c91f4180ef91`.

## Microphone architecture / far-field / tonal / AEC checkpoint

R027/R039, R035/R041, R036/R038 and R042/R044 add four exact execution/review
pairs covering bounded capsule/acoustic-path architecture, far-field scenario
coverage, sampled tonal/headroom decisions and AEC control metrics. Reviewers
reconstruct the declared candidate independently and reject hidden or extra
assertions. No thermoviscous model, measured room/wind, intelligibility,
realized filter, perceptual score, physical measurement, L3/L4 or Human
acceptance is claimed.

Focused regressions: 30 PASS and 38 PASS. Final fixed-source regression: 434
PASS in 1198.927 seconds. Six semantic routes and six dark/light fixed-
environment screenshot/basic-accessibility routes pass. The visual gate first
failed closed because a complete service assessment nearly consumed its whole
ten-second freshness budget. Matrix registry reuse and overlapping the bounded
loopback provider probe reduced assessment from about 9.86 seconds to 6.36
seconds while retaining start-time aging and stale-state rejection.

Inventory: 95 Skills, 95 Methods, 53 role suites, 423 cases, 49 roles with a
suite and 51 without one. Speaker CoE is 18/18 and Microphone CoE is 18/18.
Installed truth remains L1=100, so H0001/P02 is unfinished.

Private transcript
`.aeris/evidence/H0001-microphone-completion-final-full-tests.log`, SHA-256
`87c2c52f5e48e12e99304af8e4e7e90196c382bcfca80d56428975f802c99f7b`.
GitHub CI receives a 75-minute total job budget after otherwise-green Windows
and Ubuntu runs were cancelled in retained tail smoke gates at 50 minutes. No
gate is deleted or weakened. No Core/main/PR32 mutation, raw Evidence, SQLite,
measurement or binary is included.

## Product Chief wave 1 construction checkpoint

R045 Medical Hearing Aid, R046 OTC Hearing Aid / PSAP, R047 Assistive Listening
/ Auracast and R049 ANC Over-Ear now have product-specific execution suites.
Their decisions are materially different: prescribed acoustic fitting budget,
consumer self-fit/output control, broadcast latency/clock/receiver diversity,
and circumaural seal/ANC/excursion/pressure respectively. R069, R070 and R081
provide exact new review capabilities; R005 provides a separate over-ear review
capability without reusing TWS assertions.

All 24 Product architecture records now use an empty applicable-standard list
until task-specific legal metadata establishes family, edition, region,
provenance, rights and linkage. The prior blanket IEC 60268-5/4 assignment is
removed from generated product packs and authored knowledge derivations.

Final focused gate: 34 PASS. Fixed-source regression: 450 PASS in 1444.273
seconds. Six semantic and six dark/light screenshot/accessibility routes pass.
Inventory: 103 Skills, 103 Methods, 61 role suites, 459 cases, 56 roles with a
suite and 44 without; Product Chiefs are 5/24. Installed truth remains L1=100,
so H0001/P02 remains unfinished.

Private transcript `.aeris/evidence/H0001-product-chiefs-wave1-full-tests.log`,
SHA-256 `9000048c69dcc707764b0207b29baaf6a2beafa27cfd4880c0b50795c13d43bc`.
No Core/main/PR32 mutation, raw Evidence, SQLite, measurement or binary is
included.
