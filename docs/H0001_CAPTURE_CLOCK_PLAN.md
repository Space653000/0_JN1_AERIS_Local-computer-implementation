# H0001 capture continuity / clock contract — implementation plan

Fixed starting point: ff9a7f555cef2423727d52ee9873fa16100d1cb0, Draft PR33.
Origin: H0001 sections 4, 7, 8, 9 and 12; R032 owns channel ordering and
capture continuity, R031 owns digital sample/PDM clock feasibility. This tranche
adds bounded R032 execution and independent R031 clock-contract review, not
complete PDM noise/ADC ENOB expertise or whole-role L3. Existing Core stays
read-only; existing qualification seals fail closed on source drift.

## Input / trust boundary

An explicitly synthetic or user-supplied-unverified record, never hardware IO.
Model ID `FIRST_SAMPLE_CAPTURE_TIMESTAMP_V1`. Every timestamp denotes the first
sample acquisition instant in a shared monotonic reference clock, not callback
arrival. Callback-only or unrelated timestamp clock domains are unsupported.
All times are relative integer nanoseconds (0..2**53-1); sample/frame counters
also safe JSON integers. Validate bool separately from int. Limit input to
2..16 unique channels and 2..128 frames per channel.

Required global parameters: nominal PCM sample rate (8000..192000 integer Hz),
positive integer frame_samples (1..8192), PCM sample width and slot width
(16/24/32 bits, sample width <= slot width), ordered expected channel IDs,
observed ordered slot/channel IDs, timestamp clock identity, timestamp kind,
timestamp resolution_ns, allowed rate error_ppm, allowed alignment_skew_samples,
maximum delivery_latency_ms, and maximum nominal_rate_timing_residual_ns.
Require reference_rate_assumption=`UNVERIFIED_REFERENCE_TIMESCALE` and identical
capture/delivery reference clock IDs. All estimated rates are relative to that
supplied timebase, never absolute oscillator accuracy or calibrated seconds.

Require PDM clock_hz and integer decimation_ratio with explicit
`PDM_INTEGER_DECIMATION` mode: PDM_clock / ratio must equal nominal PCM rate.
This is only a clock-rate relationship, not proof of a decimator response,
noise shaping, filtering, quantization noise, ENOB or anti-alias performance.

Each channel has a unique expected ID and ordered records containing frame_seq,
first_sample_index, sample_count, capture_timestamp_ns and delivery_timestamp_ns.
Require equal frame count across channels for aligned comparison. Counters do
not wrap in this bounded model; wraparound requires a separate declared adapter.
Sample_count must be a positive integer but a nonmatching frame size is a reported
continuity defect, not silently padded or dropped. Arrival before capture or
non-increasing capture timestamps is invalid input, not a passing empty result.

## Execution / engineering distinctions

1. Preserve and compare expected vs observed slot order. Channel mismatch is a
   mapping defect; labels alone never prove physical microphone wiring.
2. For each adjacent channel record pair compare frame_seq increment to 1 and
   next first_sample_index to previous first_sample_index + previous sample_count.
   Report skipped/duplicated frame counters and sample gaps/overlaps separately.
   Missing transport metadata cannot be called acoustic DOA instability.
3. Rate estimate per channel uses (last sample_index - first sample_index) /
   (last capture_time - first capture_time). Do not estimate rate from number of
   received frames, since a dropped frame would masquerade as oscillator drift.
   Nonpositive sample advance is invalid. Retain nominal-rate error_ppm and an
   uncertainty interval using timestamp endpoint resolution (each endpoint
   +/- resolution/2). Non-identifiable intervals fail the rate policy.
4. Per-interval capture timing residual = actual elapsed_ns - sample advance /
   nominal_rate * 1e9. Accept only if abs(residual) plus one full timestamp
   resolution is <= residual allowance. A lower bound above allowance is FAIL;
   an interval crossing it is INCONCLUSIVE. This is metadata timing residual, not phase-noise
   spectral density or proven hardware aperture jitter.
5. Cross-channel skew is evaluated only for pairs with matching first_sample_index
   at each aligned frame position. Nonmatching counters are a misalignment defect,
   not an arbitrary timestamp subtraction. Bound absolute timestamp differences
   plus one full resolution, convert to samples at nominal rate, and compare to
   allowed skew. Unknown analog/channel group delay remains unresolved.
6. Delivery latency is delivery_time - capture_time, with the same +/- one full
   timestamp-resolution endpoint-difference bound and conservative acceptance.
   Distinguish it from capture
   alignment: high scheduling latency can coexist with correct acquisition timing.
7. Require all format, PDM rate, continuity, drift bound, timing residual,
   alignment and delivery policies for a bounded metadata contract accept.
   All uncertain intervals use PASS only if wholly inside policy, FAIL if wholly
   outside, and INCONCLUSIVE if crossing a policy limit. INCONCLUSIVE cannot
   yield a bounded acceptance. Preserve the state as well as boolean passed.
   Output per-channel diagnostics, each failed check, bounded margins, distinct
   counter-hypotheses, next discriminating experiment and model limitations.
   Always physical_capture_verified=false, bitstream_filter_verified=false,
   clock_phase_noise_verified=false, absolute_oscillator_accuracy_verified=false
   and role_l3_accepted=false.

## Independent role review and acceptance

R031 review reconstructs timing/rate bounds and continuity decisions directly
from original input with an independent implementation, not calls to R032's
executor or predicates copied from candidate output. Public schema validation
may be shared; the numerical decision oracle may not. Compare candidate complete
output including limitations, counters and false verification claims. Keep
existing context/source/risk constraints and explicit executor conflict rejection.

Authored role fixtures use small rational integer cases with manual expectations:
48 kHz / 480 samples / 10 ms frames; PDM 3.072 MHz / 64; stereo aligned zero
offset; one-sample channel skew; slot swap; one missing frame vs genuine rate
error; sample overlap; variable frame size; high delivery latency with correct
capture timing; timestamp quantization that makes rate bound inconclusive;
PCM packing mismatch; wrong decimation rate; callback/unrelated-clock refusal;
nonfinite/bool/empty/duplicate/wrap input refusal; tampered decision/check/bound
and fake physical acceptance rejection. R032 asks transport-disposition questions;
R031 asks whether clock/rate/uncertainty assertions survive independent review.

Run both role suites, then actual SQLite workflow -> qualified R031 Pod ->
execution -> evidence -> independent challenge/disposition -> report -> memory
-> reproduction. No new fixed-PASS company challenge and no ninth challenge
family is introduced. Add missing-reviewer/conflict/stale-seal negative tests.

## Delivery / rollback / unresolved breadth

Implementation is additive: new modules, two Skills/Methods, two suites, explicit
role profile/pack/router mappings and inventory tests. Do not modify live service
or Core; revert only this new commit if necessary, retaining all local evidence.
All artifacts stay under the authorized root; public handoff only sanitized
counts/hash references. Test before commit; scan and push only H0001 branch.
Run focused tests, full regression and new Windows/Ubuntu CI; keep six HTTP routes
available. Actual acquisition, calibration, driver IO, ADC/PDM noise, filter
response and comprehensive profession-level acceptance remain unproven; their
software-model portions stay future software gaps, not external blockers.

## Independent plan review disposition

Accepted P1: allowance+resolution was only compatibility, not guaranteed
compliance. Replaced it with conservative upper-bound acceptance and explicit
INCONCLUSIVE for crossing intervals, including delivery latency. Add a 150 ns
residual / 100 ns allowance / 100 ns resolution oracle: not PASS.

Accepted P2: monotonic time is not calibrated frequency. Restrict rate estimates
to explicitly unverified reference timescale, seal that assumption and reject
unknown/different capture/delivery clocks. Rename jitter to nominal-rate timing
residual so steady rate offset is not called aperture jitter. Add negative and
false absolute-accuracy claim cases. Review independence is a same-model isolated
read-only role separation, not qualified Human approval.

Implementation review also found that nearest rounding could zero a tiny true
uncertainty interval, and generic relative float tolerance could accept incorrect
large integer gap counts. Intervals now round outward onto a 1e-9 display grid
and, if necessary, outward again at binary float conversion. Policy decisions
remain exact rational comparisons. Counter integers are type/value exact; the
independent reconstruction's deterministic displayed numbers are exact as well.
The authored 1.000001 ms upper endpoint is represented by the next outward
binary float 1.0000010000000001, not by an inward nearest conversion.

## Implemented checkpoint and verification

R032 execution and R031 independent review are integrated through Role Packs,
Skills, Methods, sealed role suites, capability-driven Pod routing, SQLite
workflow, Evidence, review status and reproduction. R032 has 17 cases; R031 has
14 independently authored review cases. Focused integration/maturity tests: 21
PASS. Seeded 24-variation exact reconstruction and the two review-discovered
counterexamples are permanent regressions.

Pre-compaction regression: 371 tests PASS in 403.908 seconds, finished
2026-09-04T21:45:39.084352+00:00. Local-only transcript:
`.aeris/evidence/H0001-capture-clock-full-tests.log`; SHA-256
`685be254f92dcb8fc0e4d89323e8e0b019704fa75dba5aa26b2f1b681cf13dea`.
That transcript predates the fixture mutation engine and is retained as history.
Final fixed-source regression: 372 tests PASS in 396.918 seconds, finished
2026-09-04T21:55:29.178500+00:00. Local-only transcript:
`.aeris/evidence/H0001-capture-compact-full-tests.log`; SHA-256
`c9b8c9ee99f36629ebc2204851e8f56893427216185a4d7a14732c061773a9a9`.
Six semantic browser routes and six exact-repeatability screenshot routes also
PASS locally. The live supervisor was not replaced.

Source inventory is now 67 executable Skills/Methods, 25 role suites and 311
role cases. Current installed maturity remains L1=100, L2/L3/L4=0 because source
changes invalidate prior local receipts. Seventy-five roles still lack a current
role-domain suite. This checkpoint is not H0001 or P02 acceptance.

Role-review fixtures store one authored base candidate and bounded exact-path
mutations. The acceptance factory validates unique paths, existing fields and
bounded mutation count before applying them to a deep copy. This avoids copying
the entire candidate into each review scenario while retaining explicit,
machine-readable differences and the same independent expected decisions.
