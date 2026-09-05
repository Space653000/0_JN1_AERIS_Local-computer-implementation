---
name: tws-fit-anc-call-baseline
description: Run bounded local TWS seal, hybrid ANC delay, outward microphone wind/call, excursion and occlusion calculations from explicit engineering inputs.
---

# TWS fit / ANC / call baseline

Use the AERIS Skill runtime with `tws-fit-anc-call-baseline`. Supply every field
in `input.schema.json`; values carry the units in their field names. Obtain
parameters and limits from the task, not from an invented standard or measurement.

1. Validate units, ranges, provenance and the stated model assumptions.
2. Execute the local calculation. Numerical `result: PASS` means the calculation
   completed; inspect `values.disposition` and every margin for the design result.
3. Preserve input/output hashes, required revisions and unresolved items in the
   task Evidence. Compare wind versus stationary ambient noise: identical call
   SNR can require different FF/FB topology decisions.
4. Re-run after the actual revised inputs; an unchanged rejected hypothesis is
   not accepted merely because a report or review record exists.

Method contract: `methods/roles/tws-fit-anc-call-baseline.json`.
Independent numerical and counterhypothesis tests: `tests/test_tws_domain_method.py`.

The model assumes a single-pole seal leak, a single unity-gain feedback crossover,
uncorrelated noise, and an outward mic shared by feedforward ANC and call capture.
Supplied excursion and occlusion values are estimates, not new measurements.
Multiple crossover/nonlinear stability, actual in-ear fit, microphone transfer
functions, calibration, clinical claims and production acceptance remain outside
this calculation. Tool layer is FREE_LOCAL_BASELINE; this is not role L3 or L4.
