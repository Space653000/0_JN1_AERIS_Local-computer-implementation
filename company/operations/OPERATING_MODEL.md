# AERIS Company Operating Model

## Operating loop

```text
Human Objective
→ Requirement Decomposition
→ Current Standards / Historical Cases / Product Constraints
→ Temporary Engineering Pod
→ Hypotheses
→ Calculation / Simulation / Measurement
→ Evidence Bundle
→ G0 Contract
→ G1 Numerical
→ G2 Domain
→ G3 Regression
→ G4 Independent Review
→ G5 Human Approval when required
→ Release
→ Reproduction
→ Knowledge update
```

## Authority

- R0 read-only analysis: automatic + audit.
- R1 reversible local change: automatic with tests/diff.
- R2 controlled execution: preconditions + review/confirmation where needed.
- R3 hardware-risk action: explicit Human approval.
- R4 formal/customer/external release: independent review + Human signature.

## Company health

Allowed health states: HEALTHY, DEGRADED, FAILED, UNKNOWN, NO_HEARTBEAT, STALE, NOT_CONFIGURED, BLOCKED.

UI may not manufacture HEALTHY; status must come from live evidence.
