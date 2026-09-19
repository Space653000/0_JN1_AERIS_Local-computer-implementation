# measurement-uncertainty-budget-baseline

GUM-style (Guide to the Expression of Uncertainty in Measurement)
combined and expanded uncertainty: combined standard uncertainty
`uc=sqrt(sum(ui^2))` (root-sum-square of independent components),
expanded uncertainty `U=k*uc` for a declared coverage factor `k`
(`k=2` approximates ~95% coverage for a normal distribution).

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("measurement-uncertainty-budget-baseline", params)`.
3. Report both the combined standard uncertainty and the expanded
   uncertainty against the declared budget.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes declared components are independent
standard uncertainties. It does not verify that independence assumption,
does not distinguish Type A from Type B contributions, and is not a
substitute for an empirical gage R&R or interlaboratory comparison study.
