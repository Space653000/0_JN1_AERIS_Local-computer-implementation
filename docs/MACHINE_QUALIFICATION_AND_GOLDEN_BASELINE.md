# AERIS Machine Qualification + Acoustic Golden Baseline

This document defines the exact scope of the first deterministic machine-qualification and acoustic Golden regression baselines.

## Machine qualification baseline

`config/machine_qualification.v1.json` defines workload requirements. `aeris_runtime/machine_qualification.py` evaluates detected facts without using an LLM.

The baseline checks only facts that can be measured deterministically from the current machine inventory, including:

- supported machine profile;
- RAM;
- free disk capacity;
- Python version;
- required executable presence;
- NVIDIA identity and VRAM where applicable.

The baseline produces per-workload states:

```text
QUALIFIED_BASELINE
NOT_QUALIFIED
BLOCKED_INCOMPLETE_EVIDENCE
NOT_APPLICABLE
```

`QUALIFIED_BASELINE` is not `VERIFIED`. It does not prove sustained inference stability, latency, thermal headroom, reboot recovery, hard-offline behavior, proprietary software/license readiness, instrument connectivity or calibration validity. Those require separate real-machine Evidence.

`python -m aeris_runtime machine detect --write` embeds this qualification result into the deployment report.

## Acoustic Golden regression baseline

`golden/acoustics/v1/manifest.json` is a versioned deterministic regression suite for the current frequency-response Skills. Every fixture is pinned by SHA-256 before execution.

The baseline includes:

- valid measurement import;
- deterministic FR numerical output;
- a passing requirement case;
- a deliberately failing regression case;
- malformed duplicate-frequency rejection.

`aeris_runtime/golden_acoustics.py` executes the real Skill implementations and compares selected expected outputs. CI fails if the fixture hash changes or a deterministic output regresses.

This is not a production-complete Speaker/Microphone Golden Dataset. Production coverage still requires product-, transducer-, fixture-, chamber-, direction-, distance-, noise-, language-, tolerance-, uncertainty- and calibration-specific cases with reviewed provenance.

## Evidence semantics

These baselines may be marked `TESTED` only for their automated deterministic scope. They must not be promoted to real-machine or acoustic-domain `VERIFIED` without the corresponding external Evidence.
