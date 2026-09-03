# R030 Microphone Audio Circuit Architect

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

Refer analog microphone noise and headroom through bias, gain and ADC interfaces

### Failure mechanisms to distinguish

- input/output noise mixed across gain stages
- bias impedance shifts low-frequency response

### Competing explanations and discriminating experiments

- supply ripple rather than capsule self-noise
- common-mode conversion rather than differential signal

### Role-specific uncertainty

- noise-source correlation and component tolerance

### Neighboring role ownership

- R012: Choose speaker signal-chain gain and impedance architecture from output noise and headroom budgets
- R031: Allocate ADC/PDM clock and quantization noise without confusing bit depth with effective resolution
