---
name: microphone-capture-clock-domain-review
description: Independent counter/timestamp/rate-bound consistency; not absolute clock accuracy, PDM filtering or ADC noise
---

# R031 capture-clock contract

1. Read input.schema.json and the Method at ../../methods/roles/microphone-capture-clock-domain-review.json. Proceed only with first-sample acquisition timestamps on one explicitly unverified reference, not callback timestamps.
2. Reconstruct every candidate interval and decision from the supplied original records; reject missing, tampered or self-asserted physical/absolute-frequency claims.
3. Preserve INCONCLUSIVE whenever a supplied uncertainty interval crosses a policy. Calculation completion is not engineering compliance.
4. Seal inputs, Method/source hashes, output, counter-hypotheses and independent review. Finish this bounded step only when evidence integrity and reproduction pass; report missing review explicitly.

For model assumptions, negative scenarios and unresolved scope, consult ../../docs/H0001_CAPTURE_CLOCK_PLAN.md. Qualified hardware/clock calibration, ADC/PDM noise and whole-role L3 remain outside this contract.
