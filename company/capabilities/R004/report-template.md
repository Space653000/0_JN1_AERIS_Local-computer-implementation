# R004 Product Audio System Architect

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

Resolve product-level playback/capture interfaces and end-to-end audio latency budgets

### Failure mechanisms to distinguish

- individually passing blocks exceed end-to-end delay
- echo-reference placement mismatch

### Competing explanations and discriminating experiments

- transport buffering rather than DSP cost
- mechanical coupling rather than AEC tuning

### Role-specific uncertainty

- clock drift and subsystem budget covariance

### Neighboring role ownership

- R001: Resolve conflicting system acoustic requirements through a traceable budget and architecture decision
- R005: Choose bounded DSP architecture consistent with signal bandwidth, delay and stability constraints
