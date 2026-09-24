# erb-auditory-filter-bandwidth-baseline

Equivalent Rectangular Bandwidth (ERB) auditory-filter model (Glasberg &
Moore, 1990): `ERB(f) = 24.7*(4.37*f_kHz+1)`, and the ERB-rate/Cams
position on the auditory frequency scale:
`21.4*log10(4.37*f_kHz+1)`. Checks a declared/measured critical-bandwidth
claim against this standard model prediction.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("erb-auditory-filter-bandwidth-baseline", params)`.
3. Report the predicted ERB and whether the claimed value matches within
   the declared tolerance. A deviation outside the model's fitted range
   (roughly 100 Hz-10 kHz) is flagged as `MODEL_OUTSIDE_FITTED_RANGE`,
   not silently trusted.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: a measurable psychoacoustic descriptor
(auditory filter bandwidth), not a listener's subjective preference,
discomfort, or annoyance judgment -- those require a real listening
panel and are explicitly out of scope for this bounded calculation.
