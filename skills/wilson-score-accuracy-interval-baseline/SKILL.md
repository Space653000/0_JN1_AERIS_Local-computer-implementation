# wilson-score-accuracy-interval-baseline

Wilson score confidence interval (Wilson 1927) for a binomial
proportion: given `k` correct predictions out of `n` total, computes a
95% CI that behaves correctly near 0/1, unlike the naive normal-
approximation interval.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("wilson-score-accuracy-interval-baseline", params)`.
3. If the interval's lower bound falls below the declared minimum,
   report the accuracy claim as
   `ACCURACY_CLAIM_NOT_SUPPORTED_AT_THIS_TEST_SET_SIZE` -- do not present
   the point accuracy alone as sufficient evidence.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: checks statistical support for a point
accuracy given test-set size. It does not verify the test set is
representative of deployment conditions, does not detect data leakage
between training and test, and is not a generalization guarantee.
