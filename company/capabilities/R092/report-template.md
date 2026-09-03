# R092 Laboratory Instrument Controller

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

Plan safe instrument sequences with verified limits, acquisition provenance and explicit IO authority

### Failure mechanisms to distinguish

- dry-run output called physical reading
- stimulus exceeds fixture safety limit

### Competing explanations and discriminating experiments

- driver range mismatch rather than DUT failure
- calibration expiry rather than sensitivity drift

### Role-specific uncertainty

- instrument range, calibration and synchronization

### Neighboring role ownership

- R091: Execute deterministic test automation with bounded resource, timeout and evidence contracts
- R079: Build traceable uncertainty and gage R&R budgets with correct references and correlations
