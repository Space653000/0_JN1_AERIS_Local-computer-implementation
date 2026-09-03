# AERIS Construction Supervision Loop

## Purpose

AERIS local construction and AERIS supervision must be connected by durable repository evidence, not by a chat-only completion summary.

The intended loop is:

```text
Codex builds locally in C:\0_JN1_AERIS
→ local commit
→ explicit Human supervision-handoff request
→ privacy/secret screen
→ push Implementation work to a non-main review branch
→ add curated handoff snapshot
→ open Draft PR
→ ChatGPT reviews actual diff + CI + snapshot
→ Codex repairs the same review branch
→ repeat until supervision passes or a true external/Human gate remains
```

This is the permanent construction/inspection bridge for machines that can access the two canonical AERIS repositories.

## Default rule remains no push during construction

Professional-company build phases may say `Do not push GitHub from the local build phase`. That remains the default.

A push is allowed only after the Human explicitly asks for a **supervision handoff**. That explicit request creates a narrow exception for the Implementation repository only.

The exception does **not** authorize:

- writing or pushing canonical Core;
- direct push to `main`;
- merging the review PR;
- publishing secrets, private engineering data, raw user/customer data or unnecessary local machine artifacts.

## Review surface

Do not create a second copy of the whole repository under a new folder merely to show progress.

The correct review surface is:

1. the actual Implementation source changes on a dedicated branch;
2. a Draft PR against `main` so the diff is inspectable;
3. a small curated handoff directory for machine-readable status.

Recommended handoff path on the review branch:

```text
handoff/construction/<handoff-id>/SUMMARY.md
handoff/construction/<handoff-id>/SNAPSHOT.json
```

The source changes themselves remain in their normal repository paths. Do not duplicate them into the handoff directory.

## Required handoff snapshot

`SNAPSHOT.json` must record at least:

- handoff ID and phase ID;
- remote Implementation `main` SHA at handoff;
- local construction commit SHA;
- merge-base SHA;
- changed-file list;
- maturity counts;
- executable Skill / Method / Golden / Negative / Regression counts;
- test summary;
- unresolved capability gaps;
- external/Human gates;
- local-only artifacts intentionally excluded from GitHub;
- an Evidence manifest using hashes/pointers instead of raw private evidence where appropriate;
- the exact review question for the supervisor.

`SUMMARY.md` is the compact human-readable counterpart. It may summarize results, but its claims never override code, tests, Evidence, or the machine-readable snapshot.

## Privacy and repository hygiene

This repository is a review transport, not a dump of the local machine.

Before push, screen the intended branch for secrets and private/raw data. Keep local-only by default:

- `.env` and credentials;
- keys/certificates/tokens;
- SQLite databases and local runtime state unless a deliberately sanitized fixture is required;
- raw logs containing machine/user identifiers;
- raw user measurements or customer data;
- user documents not deliberately approved for public version control;
- unnecessary binaries, caches and generated runtime artifacts.

When evidence must stay local, publish only a safe manifest containing its type, provenance class, SHA-256, creation method/version and local Evidence pointer.

## Draft PR semantics

A Draft PR means only:

> the current local construction is available for independent review.

It does **not** mean:

- the Build Phase is complete;
- the maturity claim is correct;
- L4 is verified;
- main is ready to merge;
- real hardware/calibration/Human approval has happened.

## Supervisor review order

The supervisor should review in this order:

```text
remote main baseline
→ Draft PR changed files/diff
→ handoff SNAPSHOT.json
→ tests/CI
→ role maturity truth
→ Skills/Methods implementations
→ Golden/Negative/Regression quality
→ Evidence/verification chain
→ Product/Speaker/Microphone/Expert/Ops coverage
→ unresolved gaps and false-green risks
```

The supervisor should challenge apparent mass completion, especially cases where many roles share one shallow executable path, synthetic fixtures merely exercise plumbing, or counts increase without materially different domain competence.

## Repair loop

If review finds gaps, Codex repairs the **same review branch**, updates the handoff snapshot and pushes another commit. Do not start another local build from scratch unless the evidence is incompatible or invalid.

The review loop ends only when the supervisor has no remaining software-local objection for the declared scope, or the remaining items are genuine Hardware / Calibration / Licensed Tool / Human Approval / External gates.

## Configuration

The machine-readable contract is:

`config/construction_handoff.v1.json`
