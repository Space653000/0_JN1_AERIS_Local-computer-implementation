---
name: microphone-reference-noise-headroom-baseline
description: Analyze supplied microphone sensitivity references, separate room and frontend noise, and challenge deployment gain/headroom with uncertainty bounds.
---

# Microphone reference, noise and electrical headroom

1. Read the Method and exact input schema. Use RMS pressure/voltage and linear
   gain; distinguish calibration gain from the deployment analysis gain.
2. Supply noise values in a common bandwidth/weighting and output-voltage frame.
   Declare conservative relative bounds, not an invented calibration certificate.
   Total output noise and its upper bound must remain below the ADC peak range.
3. Run aeris_runtime.skills_runtime.run_skill. Report all margins, interval bounds,
   resolved/unresolved noise status and the next discriminating experiment.
4. Seal supplied inputs, provenance and output in the actual workflow. Require
   the separate role suite and independent reviewer before domain acceptance.

If subtraction is unidentifiable within uncertainty, retain a null intrinsic
noise estimate and request a quieter fixture or lower-noise frontend. Electrical
headroom is a signal-only ADC-chain estimate; noise crest factor and combined
signal/noise peak clipping remain unverified. It is not capsule AOP or physical SPL safety.
FREE_LOCAL_BASELINE never grants calibration, L4, Human approval or conformance.
