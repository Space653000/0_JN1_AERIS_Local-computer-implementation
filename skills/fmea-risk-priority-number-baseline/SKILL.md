# fmea-risk-priority-number-baseline

FMEA Risk Priority Number: `RPN = Severity * Occurrence * Detection`,
each rated on a declared 1-10 scale (AIAG-VDA FMEA handbook).

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("fmea-risk-priority-number-baseline", params)`.
3. Report the RPN against the declared maximum acceptable value. A
   high-severity failure mode should be separately flagged regardless
   of overall RPN -- RPN alone can mask severity-critical risks.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: the plain RPN arithmetic. It does not verify
cross-functional team consensus on the ratings, and does not separately
flag high-severity-but-low-RPN failure modes on its own.
