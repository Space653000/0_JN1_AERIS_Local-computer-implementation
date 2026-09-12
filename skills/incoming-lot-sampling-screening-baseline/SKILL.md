---
name: incoming-lot-sampling-screening-baseline
description: Bounded R095 supplier incoming-lot sampling risk screening
---

# incoming-lot-sampling-screening-baseline

Use only for a declared sample size, observed nonconforming count, data
source kind and declared acceptance threshold. Requires the source kind to
be measured incoming inspection data (a supplier certificate of conformance
alone is rejected, never treated as measured conformance) and computes the
exact one-sided binomial upper bound on the lot's true nonconforming
fraction (same method as `aeris_runtime.engineering.governance.reliability`
and `reliability_halt.py`), comparing it against a declared acceptance
threshold. A small sample size is penalized honestly through the width of
this interval, not through a separate ad hoc rule. This does not separate
assembly/test-system variation from incoming lot variation, verify supplier
certificate authenticity, or replace Human lot disposition.
