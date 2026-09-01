# Comparison / Requirement Verification

This Skill compares deterministic FR metrics against an explicit JSON requirement and reports PASS/FAIL plus numerical margin per check.

Supported baseline checks:

- maximum peak-to-peak dB in a band;
- maximum RMS deviation dB in a band;
- minimum average dB;
- maximum average dB.

Every PASS/FAIL includes the actual value, limit, operator and margin. This prevents a bare boolean from being treated as engineering evidence.

The current baseline does not substitute for product-specific target curves, measurement uncertainty, standards clauses, channel/spatial aggregation, environmental conditions or calibration requirements.
