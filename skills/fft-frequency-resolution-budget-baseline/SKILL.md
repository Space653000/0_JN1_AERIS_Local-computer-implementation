# fft-frequency-resolution-budget-baseline

FFT/DFT frequency-resolution relationship: `delta_f = fs/N`. Minimum
record length for a target resolution: `record_length_s =
1/delta_f_target`.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("fft-frequency-resolution-budget-baseline", params)`.
3. Report whether the planned record length achieves the target
   frequency resolution before running the acquisition sequence.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a plain rectangular-window resolution
calculation. It does not account for windowing functions (which broaden
effective resolution), does not model zero-padding interpolation, and is
not a substitute for a real acquisition verifying two closely-spaced
tones are actually resolved.
