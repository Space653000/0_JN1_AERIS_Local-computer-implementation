# adc-quantization-snr-baseline

Ideal N-bit ADC quantization SNR: `SNR(dB) = 6.02*N + 1.76`. Effective
number of bits from a measured/claimed SINAD:
`ENOB = (SINAD-1.76)/6.02`.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("adc-quantization-snr-baseline", params)`.
3. A claimed SINAD exceeding the ideal quantization limit for the
   declared bit depth is flagged -- verify measurement reference or
   noise-shaping/oversampling before trusting it.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: the simple (non-noise-shaped) quantization
formula for a full-scale sinusoidal input. It does not account for
noise-shaping/oversampling converters (e.g. sigma-delta/PDM), and does
not verify the claimed SINAD's measurement conditions.
