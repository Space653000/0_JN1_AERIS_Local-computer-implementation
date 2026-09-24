# bonferroni-significance-correction-baseline

Bonferroni multiple-comparisons correction: `alpha_adjusted =
alpha / n_hypotheses`. Checks whether a claimed p-value survives
correction for the declared number of hypotheses/comparisons tested.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("bonferroni-significance-correction-baseline", params)`.
3. A result that fails the adjusted threshold is reported as
   `RESULT_NOT_SIGNIFICANT_AFTER_MULTIPLE_COMPARISONS_CORRECTION` -- do
   not present it as significant without further replication.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes the declared hypothesis count reflects
all comparisons actually made. It does not detect undisclosed
exploratory analyses, and does not evaluate whether a less conservative
correction procedure (e.g. Benjamini-Hochberg) would be more
appropriate.
