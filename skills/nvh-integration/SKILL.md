# nvh-integration

Version: 1.0.0. Tool layer: FREE_LOCAL_BASELINE.

Integration of a sine divides amplitude by angular frequency.

Invoke with `python -m aeris_runtime.engineering.factory run-skill nvh-integration --input PATH`. Inputs must match `input.schema.json`; unknown fields, nonfinite values and out-of-domain values are rejected.

Method: `methods/engineering/nvh-integration.json`. Analytical, negative and repeated-run cases: `golden/engineering/Speaker/nvh-integration`.

Raw measurements require source, units, calibration, fixture and uncertainty. Synthetic fixture success is bounded L3 evidence and never L4. No proprietary tool execution, physical measurement or formal standards conformance is claimed.

The factory seals raw input, numerical output, method version, source SHA-256 and check results into an Evidence bundle. Role mappings and failure modes are in the manifest.
