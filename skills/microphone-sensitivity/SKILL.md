# microphone-sensitivity

Version: 1.0.0. Tool layer: FREE_LOCAL_BASELINE.

10 mV at 10 mV/Pa corresponds to 1 Pa RMS.

Invoke with `python -m aeris_runtime.engineering.factory run-skill microphone-sensitivity --input PATH`. Inputs must match `input.schema.json`; unknown fields, nonfinite values and out-of-domain values are rejected.

Method: `methods/engineering/microphone-sensitivity.json`. Analytical, negative and repeated-run cases: `golden/engineering/Microphone/microphone-sensitivity`.

Raw measurements require source, units, calibration, fixture and uncertainty. Synthetic fixture success is bounded L3 evidence and never L4. No proprietary tool execution, physical measurement or formal standards conformance is claimed.

The factory seals raw input, numerical output, method version, source SHA-256 and check results into an Evidence bundle. Role mappings and failure modes are in the manifest.
