---
name: microphone-capture-continuity-baseline
description: First-sample capture counters, slot packing, relative clock/rate intervals and scheduling latency; not driver IO
---

# R032 capture-clock contract

1. Read input.schema.json and the Method at ../../methods/roles/microphone-capture-continuity-baseline.json. Proceed only with first-sample acquisition timestamps on one explicitly unverified reference, not callback timestamps.
2. Execute the bounded metadata calculation through the local Skill/workflow engine. Keep frame loss, slot mapping, acquisition alignment and delivery latency distinct.
3. Preserve INCONCLUSIVE whenever a supplied uncertainty interval crosses a policy. Calculation completion is not engineering compliance.
4. Seal inputs, Method/source hashes, output, counter-hypotheses and independent review. Finish this bounded step only when evidence integrity and reproduction pass; report missing review explicitly.

For model assumptions, negative scenarios and unresolved scope, consult ../../docs/H0001_CAPTURE_CLOCK_PLAN.md. Qualified hardware/clock calibration, ADC/PDM noise and whole-role L3 remain outside this contract.
