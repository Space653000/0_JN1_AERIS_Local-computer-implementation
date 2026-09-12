---
name: instrument-sequence-safety-screening-baseline
description: Bounded R092 planned instrument-stimulus safety screening
---

# instrument-sequence-safety-screening-baseline

Use only for a declared planned stimulus amplitude, per-step duration, step
count and fixture safety limits. Checks whether the planned dry-run
sequence's amplitude, per-step duration and cumulative duration all clear
the declared fixture safety limits. This never executes real instrument IO
and never claims a dry-run result is a physical reading; it does not verify
fixture calibration/nameplate rating, and it does not authorize physical
execution or replace Human IO authorization.
