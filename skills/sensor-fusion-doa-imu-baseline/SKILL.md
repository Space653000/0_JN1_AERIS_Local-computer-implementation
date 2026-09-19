# sensor-fusion-doa-imu-baseline

Fuses an IMU-derived heading estimate with an acoustic direction-of-arrival
(DOA) estimate of the same true angle, via inverse-variance weighting
applied through a circular (unit-vector) mean so the fusion stays correct
across the 0/360 degree wrap boundary. Also screens the two timestamps
for excessive skew and screens the two headings for a disagreement near
180 degrees -- the classic symptom of a sign/frame-convention mismatch
between the two sensors -- flagging it instead of fusing through it.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("sensor-fusion-doa-imu-baseline", params)`.
3. Report the fused heading and its standard deviation, whether the
   timestamp skew and fused precision both meet the declared targets,
   and whether a possible frame-convention reversal was flagged.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a two-source scalar/circular fusion assuming
both estimates are conditionally independent Gaussian-like measurements
of the same true heading, already expressed in a shared sign convention.
It does not correct a detected frame-convention mismatch automatically,
does not model non-Gaussian or multimodal DOA error (e.g. front-back
ambiguity), and is not a substitute for physical bench verification
against a ground-truth heading reference.
