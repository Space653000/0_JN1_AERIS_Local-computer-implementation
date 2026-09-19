# thermal-noise-floor-baseline

Johnson-Nyquist thermal noise voltage: `Vrms = sqrt(4*k*T*R*BW)`, using
the exact SI-defined Boltzmann constant `k=1.380649e-23 J/K`. Standard
textbook physics: the theoretical noise-floor minimum a resistor at a
given temperature and measurement bandwidth can ever produce.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("thermal-noise-floor-baseline", params)`.
3. A claimed measured noise floor below this theoretical minimum is
   physically impossible (`CLAIMED_NOISE_BELOW_THERMAL_FLOOR_IMPOSSIBLE`)
   -- report it as a reference/bandwidth/temperature mismatch to
   reconcile, never as an unusually quiet circuit. Noise well above the
   thermal floor (`EXCESS_NOISE_LIKELY_NON_THERMAL_SOURCE`) is the
   expected signature of real EMI/ground/clock coupling contamination.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: gives the passive thermal-noise floor and
whether a claimed figure is physically consistent with it. It does not
diagnose which specific EMI/ground/clock mechanism causes any excess
noise, and does not account for active-component (op-amp/ADC) noise
beyond this passive floor.
