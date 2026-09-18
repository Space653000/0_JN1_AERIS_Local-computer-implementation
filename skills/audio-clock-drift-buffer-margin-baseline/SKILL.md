# audio-clock-drift-buffer-margin-baseline

Digital-audio clock-drift buffer-margin baseline: given two audio clock
domains' frequency error in ppm (parts-per-million, the standard
`error_hz/nominal_hz*1e6` definition) and a shared-buffer resync
interval, computes the accumulated sample-count drift
(`sample_rate_hz * |ppm_a-ppm_b| * 1e-6 * resync_interval_s`) and checks
it against the buffer's half-full margin before the next
resync/asynchronous-sample-rate-conversion (ASRC) correction.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("audio-clock-drift-buffer-margin-baseline", params)`.
3. Report the accumulated drift and margin. A margin that goes negative
   before the declared resync interval elapses means the buffer will
   underrun or overrun -- report it as `BUFFER_MARGIN_EXCEEDED_BEFORE_RESYNC`,
   not silently accepted.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes each clock domain holds a constant,
independent ppm error over the whole resync interval and that no
continuous ASRC correction happens in between. It does not measure real
hardware clock behavior, does not model temperature/aging-dependent ppm
drift, and is not a substitute for a measured drift trace on the actual
platform.
