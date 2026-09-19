# correlation-statistical-support-baseline

Fisher r-to-z transformation confidence interval for a claimed Pearson
correlation between an objective metric and subjective MOS:
`z=atanh(r)`, `SE_z=1/sqrt(n-3)`, 95% CI in z-space transformed back via
`tanh`. Checks whether the claimed correlation is statistically
distinguishable from zero at the declared sample size.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("correlation-statistical-support-baseline", params)`.
3. If the 95% CI includes zero, report the correlation as
   `CORRELATION_NOT_STATISTICALLY_SUPPORTED_AT_THIS_SAMPLE_SIZE` -- do
   not present it as evidence the metric predicts MOS.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: checks statistical support for a claimed
correlation coefficient. It does not compute MOS itself, does not
validate linearity assumptions, and does not account for repeated-
measures or non-independent sampling structure.
