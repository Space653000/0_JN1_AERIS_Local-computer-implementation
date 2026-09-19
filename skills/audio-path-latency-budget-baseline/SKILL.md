# audio-path-latency-budget-baseline

End-to-end real-time audio path latency budget: additive sum of encode,
packetization, network, jitter-buffer, decode and output-buffer delays,
checked against the ITU-T G.114 recommended maximum one-way transmission
time (150 ms) for acceptable conversational quality.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("audio-path-latency-budget-baseline", params)`.
3. Report the total one-way latency and whether it stays within the
   150 ms ITU-T G.114 guideline.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: plain arithmetic sum of declared fixed-value
delay components. It does not measure real end-to-end latency on actual
hardware/network, does not model adaptive jitter-buffer behavior under
real network conditions, and does not distinguish whether the
conversational-quality threshold even applies to the target application.
