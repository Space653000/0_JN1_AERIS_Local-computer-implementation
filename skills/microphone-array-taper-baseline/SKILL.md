---
name: microphone-array-taper-baseline
description: ULA amplitude taper and steering with supplied mismatch bounds and uncorrelated white-noise gain; not speech quality
---

# microphone-array-taper-baseline

Use the exact SI input contract for role R037. Run through the AERIS Skill
runtime, preserve input/source/output hashes, and retain every model limitation.
Positive channel delay retards phase under exp(j*omega*t). Do not normalize
observed response to its own peak. Preserve supplied mismatch intervals, angular
sampling and white-noise covariance assumptions. A sampled sidelobe maximum
cannot prove continuous-angle rejection or speech quality. Qualification is the
separate role suite; shared Skill PASS is not role L3 or Human approval.
