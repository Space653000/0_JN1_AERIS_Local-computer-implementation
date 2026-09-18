# arrhenius-acceleration-factor-baseline

Arrhenius reliability acceleration factor:
`AF = exp((Ea/k) * (1/T_use - 1/T_stress))`, with Boltzmann constant
`k=8.617333262e-5 eV/K` and temperatures in Kelvin.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("arrhenius-acceleration-factor-baseline", params)`.
3. Report the acceleration factor and the equivalent use-condition
   duration for the declared stress test duration.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes a single, thermally-activated failure
mechanism with the declared activation energy holds across the tested
temperature range. It does not empirically validate that activation
energy, does not confirm the dominant failure mechanism, and does not
account for non-thermal failure modes.
