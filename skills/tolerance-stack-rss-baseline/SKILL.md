# tolerance-stack-rss-baseline

Standard dimensional tolerance stack-up: given a list of independent
contributor tolerances, computes both the worst-case stack (arithmetic
sum -- every contributor at its extreme simultaneously) and the RSS/
root-sum-square stack (`sqrt(sum(t_i^2))` -- assumes independent,
near-normal contributor distributions), and checks each against a
declared maximum acceptable gap.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("tolerance-stack-rss-baseline", params)`.
3. Report both stack values and which check(s) passed. A stack that
   fails worst-case but passes RSS is a real, common, defensible
   engineering middle ground -- report it as its own disposition, not a
   simple pass/fail.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes contributor tolerances are independent
and near-normally distributed (the RSS assumption). It does not verify
that assumption, does not use measured process capability (Cpk) in place
of declared specification limits, and is not a substitute for a measured
assembled-sample distribution.
