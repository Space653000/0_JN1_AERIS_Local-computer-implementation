# porous-material-absorption-baseline

Bounded normal-incidence absorption estimate for a rigid-backed porous
layer (foam, felt, fibrous mat), from the Delany-Bazley (1970) empirical
model. Given flow resistivity, thickness and frequency, predicts the
complex characteristic impedance and propagation constant of the bulk
material, the resulting surface impedance against a rigid backing, and
the normal-incidence absorption coefficient -- then checks it against a
declared minimum target.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("porous-material-absorption-baseline", params)`.
3. Report the absorption coefficient, whether it met the declared target,
   and whether the normalized frequency parameter (`0.01 <= X <= 1.0`)
   stayed inside the model's own published validity range -- outside
   that range, or if the computed coefficient itself falls outside
   [0, 1] (a known limitation of the empirical fit at thin/low-frequency
   extremes, not a bug), the result is flagged rather than reported as a
   plain number.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: an empirical curve fit calibrated on fibrous
materials, normal-incidence and rigid backing. It is not a substitute for
measured impedance-tube data (ASTM E1050 / ISO 10534-2), does not cover
oblique-incidence or diffuse-field (random-incidence) absorption, and
does not cover an airspace-backed configuration.
