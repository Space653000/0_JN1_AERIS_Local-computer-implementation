# AERIS Construction Supervision Loop

## Purpose

AERIS local construction and AERIS supervision must be connected by durable repository evidence, not by a chat-only completion summary.

The intended loop is:

```text
Codex builds locally in C:\0_JN1_AERIS
→ local commit
→ explicit Human supervision-handoff request
→ supervisor allocates next unique H####
→ privacy/secret screen
→ push Implementation work to a new non-main review branch
→ add a new numbered curated handoff snapshot
→ open a new Draft PR
→ ChatGPT reviews actual diff + CI + snapshot
→ next Codex construction/repair prompt receives the next H####
→ repeat as an immutable review chain until supervision passes or a true external/Human gate remains
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

## Monotonic supervision numbering

Every new supervised Codex prompt must use a new repository-global handoff number:

```text
H0001
H0002
H0003
...
```

The IDs are monotonic and are never reused, including numbers from closed, abandoned or failed PRs.

Before ChatGPT issues a new Codex construction/repair prompt, the supervisor must inspect GitHub for all existing/closed `AERIS SUPERVISION HANDOFF H####` PRs and existing `handoff/construction/H####-*` records, take the largest number, add one, and put that exact ID into the Codex prompt.

Codex must independently collision-check the assigned ID immediately before pushing. If that number already exists as a branch, handoff directory, open PR or closed PR, Codex increments until it finds an unused ID and reports the actual ID used.

One handoff ID maps to one immutable review snapshot:

```text
branch:
  codex/handoff/H0007-P02-0752121

handoff directory:
  handoff/construction/H0007-P02-0752121/

Draft PR title:
  AERIS SUPERVISION HANDOFF H0007 — P02 — 0752121

ready signal:
  AERIS_SUPERVISION_HANDOFF_READY H0007
```

A later ChatGPT repair/build prompt must allocate `H0008` (or the next unused ID), create a new branch and open a new Draft PR. Do not repurpose or overwrite `H0007` for the later supervision cycle. Earlier PRs remain historical construction records.

## Review surface

Do not create a second copy of the whole repository under a new folder merely to show progress.

The correct review surface is:

1. the actual Implementation source changes on a dedicated uniquely numbered branch;
2. a uniquely numbered Draft PR against `main` so the diff is inspectable;
3. a small uniquely numbered curated handoff directory for machine-readable status.

Required handoff path on the review branch:

```text
handoff/construction/<H####>-<phase-id>-<local-sha7>/SUMMARY.md
handoff/construction/<H####>-<phase-id>-<local-sha7>/SNAPSHOT.json
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

> the current numbered local construction snapshot is available for independent review.

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
→ numbered Draft PR changed files/diff
→ numbered handoff SNAPSHOT.json
→ tests/CI
→ role maturity truth
→ Skills/Methods implementations
→ Golden/Negative/Regression quality
→ Evidence/verification chain
→ Product/Speaker/Microphone/Expert/Ops coverage
→ unresolved gaps and false-green risks
```

The supervisor should challenge apparent mass completion, especially cases where many roles share one shallow executable path, synthetic fixtures merely exercise plumbing, or counts increase without materially different domain competence.

## Repair/build continuation loop

If review finds gaps, ChatGPT issues a new Codex repair/build prompt with the next unused H####. Codex produces a new local commit/snapshot, pushes a new uniquely numbered review branch, and opens a new Draft PR. The previous Draft PR remains unchanged as historical evidence of the previous supervision cycle.

A new handoff may build on the previous handoff branch or local commit as appropriate, but it must not reuse the previous H#### branch, handoff directory or PR as the new review surface.

The review loop ends only when the supervisor has no remaining software-local objection for the declared scope, or the remaining items are genuine Hardware / Calibration / Licensed Tool / Human Approval / External gates.

## Configuration

The machine-readable contract is:

`config/construction_handoff.v1.json`
