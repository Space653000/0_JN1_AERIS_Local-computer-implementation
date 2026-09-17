# binaural-itd-spherical-head-baseline

Bounded sanity check for a claimed/measured interaural time difference
(ITD) from an HRTF or spatial-audio rendering pipeline, using the
Woodworth (1938) far-field rigid-sphere approximation as the reference:
`ITD(theta) = (a/c) * (theta + sin(theta))` for `0 <= theta <= 90` degrees
from the median plane, extended to the full circle by the sphere's own
front-back and left-right symmetry.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("binaural-itd-spherical-head-baseline", params)`.
3. Report the predicted ITD, the error against the claimed value, and
   whether it stayed inside the declared tolerance.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a rigid-sphere, far-field, low-frequency
approximation. It excludes pinna, torso and individual head-shape
effects, interaural level difference (ILD), and frequency-dependent
phase behavior above roughly 1.5kHz -- it is a first-order sanity
baseline, not a substitute for individualized HRTF measurement.
