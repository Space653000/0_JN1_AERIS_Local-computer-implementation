# H0001 Professional Depth Execution Loop

## Contract

- Scope: only tracked source and local-only verification state under
  `C:\0_JN1_AERIS`; Core is read-only and Implementation `main` is never pushed.
- Continue condition: complete the current Speaker/Microphone role batch without
  routine confirmation, then create a reversible commit and Draft-PR checkpoint.
- Checkpoint method: commit to
  `codex/handoff/H0001-P02-depth-368179b`, scan all tracked/unpushed blobs, then
  fast-forward push the same non-main branch.
- Change record: append real counts, limitations, test result and private log
  hash to `docs/H0001_PROGRESS.md` and the H0001 handoff follow-up.
- Stop rules: paid software, new external authority, destructive action, Core or
  `main` mutation, physical/Human acceptance, or three consecutive blocked
  items. A test failure is repaired; it is never relabelled as acceptance.

## Current batch: Speaker CoE digital transport and filter realization

### 1. R014/R032 bounded digital-transport decision and review

- Status: complete for this bounded capability.
- Change: implement role-specific I2S/TDM word/slot, BCLK/frame-sync,
  active-slot, service-margin and buffer-latency contracts with an independent
  capture-pipeline reviewer capability.
- Acceptance: positive, boundary, negative and counter-hypothesis cases pass;
  clock mismatch, duplicate slots, altered assertions and unsupported physical
  continuity claims fail closed.
- Verification: direct unit tests plus Role Acceptance suite replay.
- Evidence: local sealed role-domain execution receipt.
- Checkpoint: sealed suite replay, capability routing and reproduction PASS.

### 2. R024/R005 bounded filter-realization decision and review

- Status: complete for this bounded capability
- Blocked by: none.
- Change: check biquad pole radii, coefficient quantization, crossover sum and
  phase, peak headroom and group delay, with independent DSP review.
- Acceptance: exact reviewer Skill is selected by capability, review Evidence is
  sealed, and reproduction passes while unsupported full-band fixed-point,
  physical playback and Human claims remain fail-closed.
- Verification: end-to-end workflow, reviewer and Evidence tests.
- Evidence: local sealed reviewer qualification and review bundle.
- Checkpoint: exact-schema independent reconstruction rejects hidden headroom;
  Evidence seal and reproduction PASS.

## Batch gate

- Review required: fixed-source full unit suite, six-page semantic browser gate,
  dark/light screenshot/accessibility gate, secret/private-data scan, then
  Windows and Ubuntu CI on the pushed HEAD.
- Continue when: every local gate passes and the pushed Draft-PR checkpoint is
  visible; do not claim H0001 complete while any role-depth gap remains.

## Completed batch checkpoint

- Focused regression: 26/26 PASS.
- Fixed-source regression: 390/390 PASS in 732.098 seconds.
- Six real-browser semantic routes: PASS.
- Six fixed-environment dark/light screenshot repeatability and basic
  accessibility routes: PASS.
- Source inventory: 73 executable Skills/Methods, 31 role-specific suites,
  335 role cases; 29 roles have at least one domain suite and 71 do not.
- Installed company truth remains L0=0, L1=100, L2=0, L3=0, L4=0; the batch
  does not claim listener, calibrated physical, Human, role-wide L3 or P02
  acceptance.
- Local-only full-test transcript: `.aeris/evidence/H0001-tonal-full-tests.log`,
  SHA-256 `a407aab318c2814c02cea7e38ef3b4bcb6e6e6ecb62d8e5e8aeedfbfa171fb4b`.

## Continuation batch checkpoint

- R012: scalar gain-chain noise referral, source loading, minimum load and peak
  voltage/current budget.
- R013: independent reconstruction of all R012 assertions; no bench stability
  claim.
- R019: bass boost to excursion, temperature, amplifier and limiter-time
  envelope.
- R025: independent protection-envelope reconstruction; no smart-amplifier or
  durability claim.
- R022: synchronized structural/acoustic band transfer identifiability using
  dual-SNR, coherence, spread and alignment gates.
- R073: independent path review that explicitly rejects coherence-as-causality.
- Focused regression: 34/34 PASS.
- Fixed-source regression: 402/402 PASS in 918.149 seconds.
- Six semantic routes and six fixed-environment dark/light screenshot/basic
  accessibility routes: PASS.
- Source inventory: 79 executable Skills, 79 Methods, 37 role-specific suites,
  359 role cases; 35 roles have at least one suite and 65 do not.
- Local-only transcript: `.aeris/evidence/H0001-speaker-depth-full-tests.log`,
  SHA-256 `07536fe7c5c92a894df7b821a4d0ed6fa1d6eddb9ee11787857213318efe258d`.

## Room spatial continuation checkpoint

- R023/R072: multi-position decay coverage and an independent spatial review;
  no diffuse-field, full-room or physical-measurement claim.
- R026/R071: sampled room-correction bounds and independent review; no realized
  filter, audibility, calibration or physical acceptance claim.
- Focused regression: 30/30 PASS.
- Fixed-source regression: 410/410 PASS in 1011.760 seconds.
- Six semantic routes and six fixed-environment dark/light screenshot/basic
  accessibility routes: PASS.
- Source inventory: 83 executable Skills, 83 Methods, 41 role-specific suites,
  375 role cases; 39 roles have at least one suite and 61 do not.
- Installed company truth remains L0=0, L1=100, L2=0, L3=0, L4=0; H0001/P02
  remains unfinished.
- Local-only transcript: `.aeris/evidence/H0001-room-depth-full-tests.log`,
  SHA-256 `bb2ae2065c119ee1f4c4514bd0749714881db8a2bb5baf8a8fecb522ac2e88aa`.

## Speaker CoE completion checkpoint

- R014/R032: declared serial-audio format, clock, slot and buffer execution plus
  independent exact-assertion review; no electrical or physical continuity.
- R024/R005: declared biquad/crossover realization screening plus independent
  review; no full-band fixed-point runtime, playback or calibrated response.
- Focused regression: 30/30 PASS; affected exact-Skill regression: 30/30 PASS.
- Fixed-source regression: 418/418 PASS in 1091.297 seconds.
- Six semantic routes and six fixed-environment dark/light screenshot/basic
  accessibility routes: PASS. The first cold telemetry capture remained
  CHECKING at its fail-closed deadline; the unchanged gate passed after that
  assessment completed.
- Source inventory: 87 executable Skills, 87 Methods, 45 role-specific suites,
  391 role cases; 41 roles have at least one suite and 59 do not. Speaker CoE
  coverage is 18/18; Microphone CoE remains 10/18.
- Installed company truth remains L0=0, L1=100, L2=0, L3=0, L4=0; H0001/P02
  remains unfinished.
- Local-only transcript: `.aeris/evidence/H0001-speaker-completion-full-tests.log`,
  SHA-256 `5d5fa635b478bffeb546bded9f533de016bcfe63c4303f1c7ab7c91f4180ef91`.

## Microphone CoE completion checkpoint

- R027/R039: bounded microphone capsule, acoustic-port and array-spacing
  architecture execution plus independent acoustic-path review.
- R035/R041: bounded far-field distance, stationary/nonstationary noise,
  competing-speech and scalar-decay scenarios plus independent disturbance
  review.
- R036/R038: bounded sampled tonal correction, voice-band smoothing, output
  headroom and capsule-overload screening plus independent review.
- R042/R044: bounded ERLE, near-speech preservation, alignment, drift,
  double-talk, tail and nonlinear-residual screening plus independent review.
- Focused regressions: 30/30 PASS and combined 38/38 PASS.
- Final fixed-source regression: 434/434 PASS in 1198.927 seconds.
- Six semantic routes and six fixed-environment dark/light screenshot/basic
  accessibility routes: PASS. The visual gate initially exposed a real
  telemetry freshness race. Per-request registry reuse and concurrent bounded
  loopback health probing reduced complete assessment from about 9.86 seconds
  to 6.36 seconds without extending the ten-second truth window.
- Source inventory: 95 executable Skills, 95 Methods, 53 role-specific suites,
  423 role cases; 49 roles have at least one suite and 51 do not. Speaker CoE
  and Microphone CoE coverage are both 18/18.
- Installed company truth remains L0=0, L1=100, L2=0, L3=0, L4=0. These are
  analytical/synthetic bounded capabilities, not calibrated measurement,
  perceptual acceptance, role-wide L3, H0001 or P02 completion.
- Local-only transcript:
  `.aeris/evidence/H0001-microphone-completion-final-full-tests.log`, SHA-256
  `87c2c52f5e48e12e99304af8e4e7e90196c382bcfca80d56428975f802c99f7b`.

## Product Chief wave 1 checkpoint

- R045/R069: prescribed hearing-aid gain, vent loss, feedback onset, MPO and
  receiver-headroom execution plus independent acoustic-boundary review.
- R046/R070: OTC user gain, seal, target error, limiter, instruction and fit-
  repeatability execution plus independent claims review.
- R047/R081: Auracast serial latency, clock/resync skew, receiver diversity,
  packet loss and receiver-level spread plus independent transport review.
- R049/R005: circumaural fit coverage, cushion leak, hybrid-ANC margin,
  excursion, cushion compression and pressure proxy plus an exact new DSP
  reviewer capability; the TWS suite is not reused.
- Product architecture no longer assigns IEC 60268-5/4 to every product by
  default. The applicable list is empty until task-specific legal public
  metadata records family, edition, region, provenance, rights and linkage.
- Final focused gate: 34/34 PASS. Fixed-source regression: 450/450 PASS in
  1444.273 seconds. Six semantic routes and six dark/light screenshot/basic-
  accessibility routes: PASS.
- Inventory: 103 executable Skills, 103 Methods, 61 role suites, 459 cases;
  56 roles have a suite and 44 do not. Product Chief coverage is 5/24.
- Installed truth remains L0=0, L1=100, L2=0, L3=0, L4=0. No medical,
  interoperability, physical-fit, listener, calibrated, Human, L3, H0001 or
  P02 acceptance is claimed.
- Local-only transcript: `.aeris/evidence/H0001-product-chiefs-wave1-full-tests.log`,
  SHA-256 `9000048c69dcc707764b0207b29baaf6a2beafa27cfd4880c0b50795c13d43bc`.

## Product Chief wave 2 checkpoint

- R050/R082: local gaming-headset sidetone, boom, crosstalk, voice-SNR and
  output-headroom execution plus independent communication-budget review; no
  network/codec, plosive, physical-call or Human acceptance.
- R051/R077: smartphone hand-blockage, water-mesh, echo-coupling, orientation,
  excursion and call-SNR execution plus independent port/mesh review; no
  physical transfer, AEC, population or Human acceptance.
- Focused regression: 38/38 PASS. Fixed-source regression: 458/458 PASS in
  1600.379 seconds. Six semantic routes and six dark/light screenshot/basic-
  accessibility routes: PASS.
- Inventory: 107 executable Skills, 107 Methods, 65 role suites, 477 cases;
  60 roles have a suite and 40 do not. Product Chief coverage is 7/24.
- Installed truth remains L0=0, L1=100, L2=0, L3=0, L4=0; H0001/P02 remains
  unfinished and no physical/calibrated/perceptual/Human acceptance is claimed.
