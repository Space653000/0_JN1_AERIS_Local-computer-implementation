---
name: acoustic-dataset-screening-baseline
description: Bounded R085 sample-rate-consistency and split-leakage screening
---

# acoustic-dataset-screening-baseline

Use only for declared sample-rate-uniformity/resampling flags and a
declared duplicate-source count across dataset splits. Requires mixed
sample-rate channels to be explicitly resampled before combining, and
requires the duplicate-source count across splits to be exactly zero. This
does not perform a full ingestion-pipeline audit and does not authorize
Human dataset-release sign-off.
