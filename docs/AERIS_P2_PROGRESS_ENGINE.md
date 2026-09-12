# P2 — Progress Engine (concrete acceptance criteria)

Like P1 before it, `config/progress_truth.v1.json` reserves ids P2.1-P2.7
with no written definition anywhere in the repo. This document defines them.

## Why this phase exists

Building out P0/P1 this session exposed a real weakness in the otherwise
excellent Progress Truth design (`aeris_runtime/progress_truth.py`): the
*evaluation* is rigorous and fail-closed, but the *Evidence records themselves*
were hand-authored JSON files, one per item, written by whoever is doing the
work. That is slow, repetitive, and — more importantly — trusts the author to
honestly re-run every check rather than copy-paste a prior PASS. A "Progress
Engine" should make **producing** Evidence as trustworthy as **consuming** it.

## P2.1 — Automated Evidence generator, not hand-authored JSON
**Requires:** a single command that runs the real checks for a named set of
P0/P1 items and writes schema-correct `PROGRESS_TRUTH.json` + per-item Evidence
files itself, so a human/agent never hand-types a `"result": "PASS"`.
**Status: this session's target.** See `aeris_runtime/progress_verify.py`.

## P2.2 — Every run re-checks everything already claimed PASS
**Requires:** running the generator doesn't just add new items; it
re-verifies every item the contract knows about against the *current* source
tree and demotes anything that no longer holds, so stale PASS claims cannot
survive a regression silently.
**Status: this session's target**, folded into P2.1's implementation.

## P2.3 — Progress history, not just current snapshot
**Requires:** being able to see the score trend across the session's commits,
not only the latest state.
**Status: gap.** Timestamped Evidence filenames already give an implicit
history on disk; a rollup script/view is not built. Deferred past this tick.

## P2.4 — Progress Center UI can trigger re-verification
**Requires:** `/progress` lets a human re-run the checks from the browser
instead of needing a terminal.
**Status: gap, deliberately deferred.** Running arbitrary local checks from an
HTTP handler is a real attack-surface/safety question (an unauthenticated
loopback endpoint that executes test suites and writes files) that deserves
its own careful design, not a rushed add-on. Left for explicit Human
prioritization rather than done quickly and unsafely.

## P2.5 — Wired into the acceptance script
**Requires:** `scripts/local-acceptance.ps1`/`.sh` calls the generator so a
full acceptance run leaves fresh Evidence automatically.
**Status: gap.** Reasonable next increment once P2.1 is proven; not done this
tick to keep the change small and reviewable.

## P2.6 — Tests for the generator itself
**Requires:** the generator's checks are themselves tested (e.g. a forced
failing check correctly demotes an item to UNKNOWN/FAIL, not silently PASS).
**Status: this session's target**, `tests/test_progress_verify.py`.

## P2.7 — Documented so the next session doesn't reinvent it
**Requires:** this document plus inline docstrings in the generator.
**Status: this document + progress_verify.py docstrings.**

## Sequencing this tick
P2.1 + P2.2 + P2.6 (the generator itself, re-check-everything behavior, and
its own tests) are the tractable, self-contained slice. P2.3-P2.5 are real
but each opens its own design question (history storage/view, an HTTP
attack-surface decision, and a script-wiring change touching the acceptance
path) and are left open rather than rushed.
