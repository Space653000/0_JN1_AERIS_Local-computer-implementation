# thermal-rc

Version: 1.0.0. Tool layer: FREE_LOCAL_BASELINE.

At one thermal time constant the rise is 1-exp(-1) of steady state.

Invoke with `python -m aeris_runtime.engineering.factory run-skill thermal-rc --input PATH`. Inputs must match `input.schema.json`; unknown fields, nonfinite values and out-of-domain values are rejected.

Method: `methods/engineering/thermal-rc.json`. Analytical, negative and repeated-run cases: `golden/engineering/Speaker/thermal-rc`.

Raw measurements require source, units, calibration, fixture and uncertainty. Shared synthetic Skill fixtures establish only the stated Skill baseline. Role L3 requires separate role-specific domain acceptance with independent decision oracles and qualified bounded review. L4 requires real instrument/calibration/Human evidence. No proprietary tool execution, physical measurement or formal standards conformance is claimed.

The factory seals raw input, numerical output, method version, source SHA-256 and check results into an Evidence bundle. Role mappings and failure modes are in the manifest.
