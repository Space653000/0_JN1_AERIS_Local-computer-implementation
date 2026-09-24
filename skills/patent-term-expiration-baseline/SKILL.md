# patent-term-expiration-baseline

US utility patent term (35 U.S.C. 154(a)(2)): 20 years from the earliest
claimed filing date, excluding Patent Term Adjustment (PTA) or Patent
Term Extension (PTE).

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("patent-term-expiration-baseline", params)`.
3. A claimed expiration that deviates from the 20-year baseline is
   flagged -- verify whether a granted PTA/PTE or terminal disclaimer
   explains the deviation before treating either date as authoritative.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: the plain statutory 20-year term. It does not
compute PTA/PTE, does not account for design or plant patent term rules,
and is not a legal opinion on actual patent status.
