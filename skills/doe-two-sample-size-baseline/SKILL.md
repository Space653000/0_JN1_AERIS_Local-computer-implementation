# doe-two-sample-size-baseline

Standard two-sample mean-comparison sample-size formula (normal
approximation): `n = 2*(z_alpha/2 + z_beta)^2 * sigma^2 / delta^2`,
where `z_alpha/2` and `z_beta` are standard-normal quantiles for the
declared two-sided significance level and statistical power.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("doe-two-sample-size-baseline", params)`.
3. Report the required per-group sample size and whether it fits the
   declared budget.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a normal-approximation formula assuming equal
variance and equal group sizes. It does not validate the assumed standard
deviation against real pilot data, does not account for non-normal or
rank-based tests, and is not a substitute for a properly designed
experiment.
