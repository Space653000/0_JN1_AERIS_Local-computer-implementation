# R005 DSP & Algorithm Director

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

Choose bounded DSP architecture consistent with signal bandwidth, delay and stability constraints

### Failure mechanisms to distinguish

- filter group delay exceeds interaction budget
- enhancement removes desired speech

### Competing explanations and discriminating experiments

- clipping before DSP rather than filter defect
- reference misalignment rather than adaptation failure

### Role-specific uncertainty

- finite-window estimates and algorithm operating domain

### Neighboring role ownership

- R024: Implement speaker EQ and crossover filters with numerical response, delay and clipping checks
- R044: Choose NR, AGC and dereverb tradeoffs without claiming perceptual quality from a single proxy
