# measurement-difference-significance-baseline

Two-independent-measurement significance z-score:
`z=(x1-x2)/sqrt(u1^2+u2^2)`. A `|z|` at or above the declared threshold
(conventionally 2, approximately 95% confidence under a normal-error
assumption) is treated as distinguishable from measurement noise.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("measurement-difference-significance-baseline", params)`.
3. A non-significant result (`DIFFERENCE_WITHIN_MEASUREMENT_NOISE`) is
   not proof of equivalence -- report it as inconclusive, not "no
   difference."
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes the two measurements were taken under
matched conditions with independent, approximately normal uncertainties.
It does not verify matched-conditions, and is not a substitute for a
full comparative study with repeated measurements.
