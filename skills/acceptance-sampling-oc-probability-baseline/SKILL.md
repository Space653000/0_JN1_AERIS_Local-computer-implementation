# acceptance-sampling-oc-probability-baseline

Binomial acceptance-sampling operating-characteristic (OC) curve point:
given sample size `n`, acceptance number `c`, and an assumed true lot
defect rate `p`, computes `P(accept) = sum_{k=0}^{c} C(n,k)*p^k*(1-p)^(n-k)`.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("acceptance-sampling-oc-probability-baseline", params)`.
3. Report the acceptance probability at the declared defect rate against
   the declared minimum acceptable value.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a single OC-curve point at one assumed defect
rate, not the full curve. It does not validate the assumed defect rate
against real supplier history, and does not account for within-lot
defect clustering.
