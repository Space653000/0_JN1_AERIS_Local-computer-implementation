---
name: reliability-halt-screening-baseline
description: Bounded R096 HALT/reliability binomial screening
---

# reliability-halt-screening-baseline

Use only for a declared trial/failure count with a stated confidence level
and acceptance threshold. Computes the exact one-sided binomial upper bound
on the true failure probability (same method as
`aeris_runtime.engineering.governance.reliability`) and compares it against
a declared maximum acceptable failure probability. This does not perform
accelerated-life (e.g. Arrhenius temperature-acceleration) extrapolation,
execute a physical HALT chamber, award role-wide L3, or replace Human
approval.
