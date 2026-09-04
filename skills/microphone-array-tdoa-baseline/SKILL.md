---
name: microphone-array-tdoa-baseline
description: Analyze supplied synchronized two-channel samples with GCC-PHAT and explicit peak/geometry ambiguity.
---

Read the Method and exact input schema before local execution. Supply a declared
band, polarity and synchronization model, geometry bounds and separate timing /
estimator-error bounds. These declarations remain assumptions, not calibration.

Preserve unresolved polarity, broad/tied peaks, aliasing and out-of-aperture arrivals.
Report planar/front-back and 3D-cone ambiguity even when a bounded estimate passes.
The domain factory seals input, Method, source hashes and output. Qualification
requires the seat-specific suite; a shared correlation Skill does not grant L3.
Keep physical/Human acceptance separate from this deterministic baseline.
