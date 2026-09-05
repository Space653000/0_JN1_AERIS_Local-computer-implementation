# R044 NR / AGC / Dereverb / Speech Enhancement Engineer

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

Choose NR, AGC and dereverb tradeoffs without claiming perceptual quality from a single proxy

### Failure mechanisms to distinguish

- AGC masks clipping
- denoiser hallucinates or removes speech detail

### Competing explanations and discriminating experiments

- level normalization rather than true improvement
- reference drift rather than dereverb gain

### Role-specific uncertainty

- out-of-distribution speech and proxy validity

### Neighboring role ownership

- R038: Tune speech capture for double-talk, spectral preservation and transient intelligibility
- R042: Choose echo-control alignment and adaptation constraints across delay and double-talk
