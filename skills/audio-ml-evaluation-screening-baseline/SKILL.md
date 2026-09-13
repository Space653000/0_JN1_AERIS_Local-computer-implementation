---
name: audio-ml-evaluation-screening-baseline
description: Bounded R084 train/test-leakage and production-robustness-claim screening
---

# audio-ml-evaluation-screening-baseline

Use only for a declared train/test source-recording overlap count and
declared production-robustness-claim/validation flags. Requires the
overlap count to be exactly zero and requires production-representative
validation before a production-robustness claim is accepted -- a
synthetic-only accuracy figure never satisfies this on its own. This does
not perform a full dataset provenance audit and does not authorize Human
model-release sign-off.
