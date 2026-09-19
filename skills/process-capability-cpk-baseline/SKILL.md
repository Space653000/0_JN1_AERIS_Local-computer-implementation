# process-capability-cpk-baseline

Process Capability Index Cpk: `Cpu=(USL-mean)/(3*sigma)`,
`Cpl=(mean-LSL)/(3*sigma)`, `Cpk=min(Cpu,Cpl)`. Standard textbook
statistical process control (SPC); unlike Cp, Cpk correctly penalizes an
off-center process.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("process-capability-cpk-baseline", params)`.
3. Report Cpk and whether it meets the declared minimum acceptable
   value before setting factory EOL decision limits.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes the declared mean/sigma are reliable
and the process is in statistical control and approximately normal. It
does not run a control chart, does not verify normality, and is not a
substitute for a real production sample study.
