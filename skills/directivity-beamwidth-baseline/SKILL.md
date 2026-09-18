# directivity-beamwidth-baseline

-N dB beamwidth from a supplied horizontal polar measurement: finds the
two angles either side of on-axis where the level first drops by the
declared threshold below the on-axis reference (linear interpolation
between measured points), and reports their angular span.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("directivity-beamwidth-baseline", params)`.
3. Report the beamwidth and whether it meets the declared coverage
   target.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a single horizontal-plane cut, linear
interpolation between measured points. It does not compute a full 3D
directivity index, does not measure vertical-plane directivity, and
does not detect pattern asymmetry beyond the two reported crossing
angles.
