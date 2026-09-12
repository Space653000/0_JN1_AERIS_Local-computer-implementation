---
name: codec-transport-screening-baseline
description: Bounded R083 jitter-buffer-margin and loss-burst screening
---

# codec-transport-screening-baseline

Use only for a declared jitter-buffer size, network jitter, consecutive
packet-loss burst length and declared acceptance thresholds. Checks the
buffer margin against a declared minimum and the loss-burst length against
the concealment algorithm's declared capability -- deliberately never
scoring loss by its average rate alone, since a burst long enough to
exceed concealment capability degrades quality far more than the same
total loss spread out as isolated drops. This does not cover a full
network-condition coverage matrix, does not execute a physical instrument
measurement, and does not authorize Human production sign-off.
