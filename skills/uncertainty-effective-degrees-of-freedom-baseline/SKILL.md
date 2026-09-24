# uncertainty-effective-degrees-of-freedom-baseline

Welch-Satterthwaite effective degrees of freedom (GUM Annex G):
`nu_eff = uc^4 / sum(ui^4/nu_i)`. Determines whether the large-sample
`k=2` coverage-factor approximation is adequate, or whether a small
effective degrees of freedom means a Student's-t coverage factor should
be looked up instead.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("uncertainty-effective-degrees-of-freedom-baseline", params)`.
3. An effective degrees of freedom below 30 flags the small-sample
   regime -- look up the correct Student's-t coverage factor rather than
   assuming `k=2`.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: computes the effective degrees of freedom. It
does not itself look up the Student's-t coverage factor, and assumes
each component's declared degrees of freedom accurately reflects its own
characterization.
