# R031 ADC / PDM / Clock / Noise Specialist

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

Allocate ADC/PDM clock and quantization noise without confusing bit depth with effective resolution

### Failure mechanisms to distinguish

- PDM clock feedthrough aliases in band
- digital attenuation hides upstream overload

### Competing explanations and discriminating experiments

- clock spur rather than acoustic tone
- ADC input clipping rather than mic saturation

### Role-specific uncertainty

- ENOB assumptions, clock phase noise and decimator response

### Neighboring role ownership

- R030: Refer analog microphone noise and headroom through bias, gain and ADC interfaces
- R032: Verify multichannel capture timestamps, channel ordering and buffer continuity
