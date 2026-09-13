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
**Status: done.** `aeris_runtime/progress_history.py`'s `compute_history()`
reconstructs the trend from the timestamped per-item Evidence files
`progress_verify` already writes under `.aeris/evidence/progress/*.json` —
no separately maintained log, so it cannot drift from reality. It groups
Evidence by `candidate_sha`, takes each item's latest capture at that sha,
and scores it against the *current* contract's `required_items` (an item
that did not exist yet at an older sha correctly shows as not-yet-passed for
that point, rather than being silently backfilled). Exposed via
`GET /api/v1/progress/history` (`aeris_runtime/controlplane.py`) and
rendered as a bar chart on `/progress` (`ui/web/progress.js`'s
`renderHistory()`/`loadHistory()`, `ui/web/progress.css`'s
`.history-chart`/`.history-bar`). Verified against the real repo: 46 distinct
commits reconstructed, chronologically sorted, matching the `overall_percent`
progression observed live across the session. Tested in
`tests/test_progress_history.py` (empty dir, chronological reconstruction,
latest-capture-wins, malformed-file tolerance, fail-closed on unreadable
contract). Wired into `progress_verify.CHECKS["P2.3"]`.

## P2.4 — Progress Center UI can trigger re-verification
**Requires:** `/progress` lets a human re-run the checks from the browser
instead of needing a terminal.
**Status: done.** Originally deferred because an unauthenticated loopback
endpoint that executes local checks and writes Evidence files was a genuine
attack-surface question. That objection is now resolved by the multi-user
auth system (see `docs/AERIS_ACCESS_CONTROL.md`): the trigger endpoint is
gated to the `"admin"` permission specifically, which only the single owner
account ever carries — no granted account, however broadly scoped, can
reach it.

Implementation: `aeris_runtime/progress_verify.py` holds a single-flight,
cooldown-protected background-thread state machine (`_WEB_TRIGGER_LOCK`,
`_WEB_TRIGGER_STATE`, `WEB_TRIGGER_COOLDOWN_S = 30.0`,
`web_trigger_status()`, `start_web_triggered_run()`) so at most one
verification run is ever in flight and a burst of clicks can't pile up
concurrent `run()` calls. `aeris_runtime/controlplane.py` exposes
`GET /api/v1/progress/reverify` (current status, any authenticated caller)
and `POST /api/v1/progress/reverify` (admin-only trigger, 202 on start or
409 if already running/in cooldown). `ui/web/progress.html`/`progress.js`
add a "重新驗證全部項目" button that only renders for the owner (checked via
`/api/v1/auth/status`'s `role` field, defense-in-depth alongside the
server-side gate) and polls the status endpoint every 3s while a run is
active, then reloads the page's data on completion. Tested at the module
level in `tests/test_progress_verify.py::WebTriggeredRunTests` (idle status,
background execution/completion, second-trigger rejection, cooldown, and
exception safety) and at the HTTP layer in `tests/test_controlplane.py`
(non-admin gets 403; owner gets 202 and can poll status to completion).
Wired into `progress_verify.CHECKS["P2.4"]`.

## P2.5 — Wired into the acceptance script
**Requires:** `scripts/local-acceptance.ps1`/`.sh` calls the generator so a
full acceptance run leaves fresh Evidence automatically.
**Status: done.** Both `scripts/local-acceptance.ps1` and
`scripts/local-acceptance.sh` invoke `python -m aeris_runtime.progress_verify`
at the end of the run, with a non-fatal warning (not a hard failure) if any
item comes back FAIL/UNKNOWN — a fresh acceptance run always leaves current
Evidence without requiring a separate manual step. Verified via
`progress_verify.CHECKS["P2.5"]` against the real scripts (`ps1=True sh=True`).

## P2.6 — Tests for the generator itself
**Requires:** the generator's checks are themselves tested (e.g. a forced
failing check correctly demotes an item to UNKNOWN/FAIL, not silently PASS).
**Status: this session's target**, `tests/test_progress_verify.py`.

## P2.7 — Documented so the next session doesn't reinvent it
**Requires:** this document plus inline docstrings in the generator.
**Status: this document + progress_verify.py docstrings.**

## Sequencing
P2.1 + P2.2 + P2.5 + P2.6 (the generator itself, re-check-everything
behavior, acceptance-script wiring, and its own tests) are done. P2.3
(history) was completed once the generator had produced enough Evidence to
make history reconstruction meaningful. P2.4 (UI-triggered re-verification)
was completed once the multi-user auth system made an admin-only gate
possible, resolving the original attack-surface objection. All of P2.1–P2.7
are now done.
