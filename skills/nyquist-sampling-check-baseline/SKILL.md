# nyquist-sampling-check-baseline

Shannon-Nyquist sampling theorem check: a signal containing energy up to
`max_signal_frequency_hz` requires a sample rate of at least
`2*max_signal_frequency_hz` to avoid aliasing.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("nyquist-sampling-check-baseline", params)`.
3. A violation is flagged as `ALIASING_RISK_NYQUIST_CRITERION_VIOLATED`
   -- verify whether an anti-aliasing filter was applied before trusting
   the dataset.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a declared-value criterion check, not a
spectral measurement of a real recording. It does not confirm whether an
anti-aliasing filter was actually applied, and does not verify the
declared maximum signal frequency against real measured content.
