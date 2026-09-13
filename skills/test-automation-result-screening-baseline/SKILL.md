---
name: test-automation-result-screening-baseline
description: Bounded R091 test-automation retry-disclosure and pass-signal screening
---

# test-automation-result-screening-baseline

Use only for a declared attempt count, final-attempt-passed flag, retry-
disclosure flag and explicit-pass-signal flag. Requires that any retries
before an eventual pass be disclosed rather than hidden behind a bare
"passed" report, and requires an explicit pass signal rather than treating
the test process merely staying alive as a pass. This does not evaluate a
full automation run's resource/timeout budget and does not authorize a
physical/production release.
