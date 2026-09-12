---
name: aeris-gate
description: AERIS local build's one-gate-at-a-time workflow — pick the next real P0-P6 item, implement it, verify it, write Evidence, commit, push, and re-align the running server. Use whenever continuing AERIS (C:\0_JN1_AERIS) build work across P0-P6, especially at the start of a session/tick or right after a commit.
---

# AERIS Gate Workflow

This encodes the workflow this project has actually used to take P0/P1 from
0% to 100% and P2-P4 to real, evidence-backed partial completion. Follow it
literally; skipping steps is how Evidence goes stale silently.

## Ground truth, not vibes

Never trust a prior session's or your own memory's claim that something is
"done." Check `GET http://127.0.0.1:8765/api/v1/progress` (or start the
server first: `& .venv\Scripts\python.exe -m aeris_runtime company open --actor <name> --start-supervisor --port 8765`).
If `truth_state` is `FAIL_CLOSED` or an item shows `UNKNOWN`, that is the
real state — do not describe it as done based on a prior report.

`docs/AERIS_P<N>_*.md` files define what each phase's items concretely mean
(P1 Kairos UX, P2 Progress Engine, P3 Golden Engineer, P4 Skill Teaching).
If the next phase (P5, P6) has no such doc yet, write one first, grounded in
real investigation of the codebase — not invented from the phase label alone.

## The loop

1. **Read real state.** `GET /api/v1/progress`, or `python -m aeris_runtime.progress_verify --dry-run` to re-check everything against current source without writing.
2. **Pick exactly one next item.** Prefer items with a real, already-built-but-never-exercised code path (see P3's history: `evaluate_role`/`RoleAcceptanceFactory` existed and were tested but nothing ever called them) over inventing new mechanism from scratch.
3. **Investigate before building.** Grep for existing functions/tests before writing new code. This project rewards finding "someone already built this, just never ran it" far more than writing new capability.
4. **If a check requires human judgment** (what counts as a "qualified independent reviewer," what a business/legal gate needs), stop and ask — don't invent a shortcut that looks like the real thing (see P3.6).
5. **Implement the smallest real slice.** Don't blend multiple P-items into one unreviewable commit.
6. **Verify live, not just via unit tests.** For UI changes, actually open the page in a browser and read the console. For backend changes, hit the real endpoint.
7. **Run the regression suite** for whatever you touched, plus `aeris_runtime core verify` (must stay `valid: true` — never edit files under `.aeris/core-reference/`, that is a read-only mirror of the canonical Core repo; put new CSS/JS in `ui/web/` instead).
8. **Commit** with a message that states what was found, what was built, and what was verified (not just what changed).
9. **Push** to the current branch (`git push origin <branch>`) — this project keeps the remote branch in sync every commit, not batched.
10. **Run `scripts\aeris-gate-cycle.ps1`** — this replaces the old manual steps 10-12 (restart the supervisor, wait for it to come up, re-run `progress_verify`, read `/api/v1/progress`, fail loudly if `truth_state` is `FAIL_CLOSED`) with one command. It exits non-zero on failure, so it's safe to chain. Pass `-SkipRestart` only if the running server is already known-aligned (rare — a fresh commit almost always needs the restart).
   - Do not hand-roll the restart again: an early draft of this exact script used `Start-Process ... -ArgumentList 'company','open',...` without `'-m','aeris_runtime'` first, which silently started no server at all. If editing this script, re-verify end to end (`GET /health` shows the new `implementation_sha`) before trusting it.
11. **Confirm the script's final line** says "Gate cycle complete" before reporting anything as done. If it warns `FAIL_CLOSED`, something was committed without matching Evidence — go back to step 8 territory and figure out what's missing before continuing.
   - **Don't commit new changes while a gate-cycle run is still in flight in the background.** It races: the script restarts the server against whatever HEAD existed when it started, then a commit lands mid-run, and by the time `progress_verify` finishes HEAD has moved past what the server is aligned to -> `runtime_candidate_mismatch`, `FAIL_CLOSED`. This isn't a script bug (it correctly refuses to lie), it's a timing mistake — happened once even while using this exact skill. If you must keep working while one runs, hold commits until it reports back, then re-run.

## Known standing gaps (do not silently "fix" without asking)

- **P3.6** (push role L2 -> L3): `role_l3_awarded`/`role_l3_accepted` is
  hardcoded `False` in over 30 independent review modules across
  `aeris_runtime/engineering/*_review.py`, not just one place — and it is
  paired with `human_approval: False` in nearly every one of them. That is
  too consistent to be an oversight; it reads as a deliberate project-wide
  stance that no automated review, however sophisticated, self-certifies
  L3 — the final award is meant to be a Human action. Do not build an
  AI-reviews-AI path that flips this to True automatically without asking
  the Human first, even though the reviewer-allocation/domain-review
  machinery to *support* a review is real and already tested.
- **P4.4**: full zh-TW translation of all 132 skills' descriptions is large
  content work, intentionally not done in one pass.
- **P2.4**: triggering re-verification from the Progress Center UI is
  deliberately deferred — an unauthenticated loopback endpoint that executes
  checks and writes files is a real design question, not a quick add-on.

## Known performance traps

`aeris_runtime.engineering.api.live_matrix()` and
`aeris_runtime.telemetry.TelemetryProjection` both cache expensive
recomputation (evidence-store validation scales with how many sealed
`RUN-*` bundles exist, which only grows). If either becomes slow again as
the evidence store keeps growing, the fix is tuning `_MATRIX_REFRESH_AFTER_S`
/ `TelemetryProjection.refresh_after_s`/`max_age_s`, not reverting to
synchronous recomputation.
