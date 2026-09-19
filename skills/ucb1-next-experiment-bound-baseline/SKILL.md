# ucb1-next-experiment-bound-baseline

UCB1 (Upper Confidence Bound) arm-selection score (Auer, Cesa-Bianchi &
Fischer 2002): `score = mean_reward + sqrt(2)*sqrt(ln(total_trials)/arm_trials)`.

## Usage

1. Read this manifest and `input.schema.json`/`output.schema.json`.
2. Call `run_skill("ucb1-next-experiment-bound-baseline", params)`.
3. A `risk_gate_passed=false` blocks the experiment regardless of the
   UCB score -- the score never overrides a failed risk gate.
4. Seal Evidence with input/output/method hashes as with any other Skill.

## Scope

Free local baseline only: assumes a stationary reward distribution per
arm. It does not itself evaluate the risk gate (that is a separate,
externally-supplied boolean), and does not guarantee the risk gate
result remains valid between evaluation and actual execution.
