# response-phase-delay

Version: 1.0.0. Tool layer: FREE_LOCAL_BASELINE.

Linear phase of a 1 ms delay has constant group delay.

Invoke with `python -m aeris_runtime.engineering.factory run-skill response-phase-delay --input PATH`. Inputs must match `input.schema.json`; unknown fields, nonfinite values and out-of-domain values are rejected.

Method: `methods/engineering/response-phase-delay.json`. Analytical, negative and repeated-run cases: `golden/engineering/DSP/response-phase-delay`.

Raw measurements require source, units, calibration, fixture and uncertainty. Synthetic fixture success is bounded L3 evidence and never L4. No proprietary tool execution, physical measurement or formal standards conformance is claimed.

The factory seals raw input, numerical output, method version, source SHA-256 and check results into an Evidence bundle. Role mappings and failure modes are in the manifest.
