# R080 Sensor Fusion / IMU / Head Tracking

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

Fuse head/IMU timing with acoustic direction while preserving coordinate-frame uncertainty

### Failure mechanisms to distinguish

- frame convention reverses direction
- timestamp skew mistaken for motion

### Competing explanations and discriminating experiments

- sensor alignment rather than DOA error
- latency rather than rotational bias

### Role-specific uncertainty

- pose covariance and synchronization error

### Neighboring role ownership

- R071: Choose binaural/spatial rendering assumptions from HRTF, head pose and temporal alignment
- R043: Estimate TDOA/DOA and beamforming feasibility subject to geometry, aliasing and channel calibration
