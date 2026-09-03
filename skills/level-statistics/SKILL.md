# level-statistics

Version: 1.0.0. Tool layer: FREE_LOCAL_BASELINE.

Equal-duration energies average linearly, not as decibels.

Invoke with `python -m aeris_runtime.engineering.factory run-skill level-statistics --input PATH`. Inputs must match `input.schema.json`; unknown fields, nonfinite values and out-of-domain values are rejected.

Method: `methods/engineering/level-statistics.json`. Analytical, negative and repeated-run cases: `golden/engineering/Microphone/level-statistics`.

Raw measurements require source, units, calibration, fixture and uncertainty. Synthetic fixture success is bounded L3 evidence and never L4. No proprietary tool execution, physical measurement or formal standards conformance is claimed.

The factory seals raw input, numerical output, method version, source SHA-256 and check results into an Evidence bundle. Role mappings and failure modes are in the manifest.
