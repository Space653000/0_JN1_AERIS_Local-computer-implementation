# rf-link-budget-friis-baseline

Friis free-space transmission equation for RF link budget:
`Pr(dBm) = Pt(dBm) + Gt(dBi) + Gr(dBi) - FSPL(dB)`, where
`FSPL(dB) = 20*log10(4*pi*d/lambda)`.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("rf-link-budget-friis-baseline", params)`.
3. Report the link margin and whether the link closes above the declared
   receiver sensitivity.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: free-space propagation with no multipath,
obstruction or body-worn attenuation. It does not certify any wireless
protocol (Bluetooth/LE Audio), does not model real-environment path
loss, and is not a substitute for a measured RSSI at the actual
deployment distance.
