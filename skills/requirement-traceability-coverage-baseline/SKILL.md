# requirement-traceability-coverage-baseline

Requirement-to-test traceability coverage ratio:
`coverage_percent = 100 * covered_requirements / total_requirements`.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("requirement-traceability-coverage-baseline", params)`.
3. Report coverage percent and uncovered count against the declared
   minimum threshold.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a declared-count ratio. It does not audit
whether "covered" links are genuine and currently passing, and does not
verify the total requirement count is complete.
