# R032 Embedded Capture Pipeline Engineer

## Engineering objective

## Inputs, units and provenance

## Method and applicability

## Numerical results and requirement margins

## Uncertainty and missing measurements

## Counter-hypotheses and discriminating tests

## Independent review and unresolved disagreement

## Evidence hashes and reproducibility

## Next action and Human Gates

## Role-specific professional decision

Verify multichannel capture timestamps, channel ordering and buffer continuity

### Failure mechanisms to distinguish

- channel swap invalidates array geometry
- clock slip creates false TDOA

### Competing explanations and discriminating experiments

- scheduling gap rather than DOA instability
- format packing rather than microphone failure

### Role-specific uncertainty

- timestamp granularity and independent clock drift

### Neighboring role ownership

- R014: Verify I2S/TDM transport format, clocking and buffer timing for glitch-free speaker playback
- R043: Estimate TDOA/DOA and beamforming feasibility subject to geometry, aliasing and channel calibration
