# test-automation-runtime-budget-baseline

Central-limit-theorem aggregate test-suite runtime budget: for `n`
independent tests each with mean duration `mean_s` and standard
deviation `std_s`, the sum's mean is `n*mean_s` and its standard
deviation is `std_s*sqrt(n)`. A `k`-sigma margin above the mean gives a
statistically grounded timeout.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("test-automation-runtime-budget-baseline", params)`.
3. Report the recommended timeout and whether it fits the declared
   maximum allowed budget.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes independent, approximately normal
per-test durations. It does not measure the actual CI runtime
distribution, does not account for shared-resource contention between
tests, and is not a substitute for real repeated-run measurement.
