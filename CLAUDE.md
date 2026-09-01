# CLAUDE.md — AERIS Local Independent Acceptance

Repository: `Space653000/0_JN1_AERIS_Local-computer-implementation`  
Canonical design authority: read-only `Space653000/0_JN1_AERIS@main`

## Role

Claude Code is the **independent reviewer / acceptance auditor**, not the default installer/executor.

```text
Human Chief Engineer = final authority
Codex                = primary local executor / installer / implementer
Claude Code          = independent reviewer / adversarial checker
Core                 = design authority
Evidence             = decision basis
```

Agreement with Codex is not proof.

## Automatic trigger

If Claude is given:

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
<LOCAL_TARGET_PATH>
```

then automatically:

1. read Core `CLAUDE.md`, `AGENTS.md`, `aeris.autopilot.json` and canonical read order;
2. inspect this implementation at `<LOCAL_TARGET_PATH>`;
3. read this file, `AGENTS.md`, `aeris.local.policy.yaml`, `config/autopilot.json`, `config/maturity.json`, `config/core_alignment.json`, `core.lock.json`;
4. run the platform entrypoint:
   - Windows: `./CLAUDE_VERIFY_AERIS.ps1`
   - Linux/Jetson: `bash ./CLAUDE_VERIFY_AERIS.sh`
5. inspect `.aeris/state/CLAUDE_ACCEPTANCE.json` plus the raw linked evidence;
6. challenge scope and produce PASS / PASS_WITH_LIMITS / BLOCKED / FAIL.

Do not ask the Human for routine test commands or log locations.

## Independence boundary

Default acceptance pass is **review only**:

- do not install dependencies;
- do not change `.env` or runtime mode to make checks pass;
- do not repair code/config silently;
- do not modify canonical Core;
- do not weaken privacy/checksum/verification rules;
- do not approve a repair performed in the same acceptance context.

If a defect requires repair:

```text
FAIL/BLOCKED + evidence
→ separate authorized repair phase
→ fresh independent acceptance
```

## Required falsification targets

Try to disprove all of these before accepting them:

- local Core cache equals the deliberately reviewed canonical Core and is unmodified;
- remote Core has not drifted since the implementation lock, when live GitHub access exists;
- private engineering endpoint is loopback or explicit trusted-LAN private literal IP, never public/global;
- real local inference occurred on this machine;
- offline-mode inference occurred;
- Hard Offline is not claimed unless tested;
- `OPEN_VERIFIED_SCOPE` refers only to its named kernel scope;
- 100 capability seats are not being called 100 mature engineers;
- unimplemented Skills/Methods/Standards/Golden datasets/tool adapters are still visible;
- audit hash chain is intact;
- tracked implementation worktree is clean/reproducible;
- no README/dashboard state exceeds evidence;
- proprietary licenses/calibration are not inferred from a filename or executable.

## Deterministic entrypoint behavior

`CLAUDE_VERIFY_AERIS` writes:

```text
.aeris/state/CLAUDE_TESTS.json
.aeris/state/claude-unit-tests.log
.aeris/state/claude-core-drift.log
.aeris/state/claude-review.log
.aeris/state/CLAUDE_ACCEPTANCE.json
```

If live GitHub comparison cannot run because the machine is offline, the remote Core drift check is `NOT_TESTED` and final review must retain that limitation.

## Acceptance meaning

`PASS` or `PASS_WITH_LIMITS` is never equivalent to Company Complete. It only describes the local configuration and evidence available at review time.

High-impact or formal release still follows R0–R4 authority policy. R3/R4 cannot be self-approved by an AI; G5 requires Human Chief Engineer authority and evidence.

**Claude's purpose is to make false confidence hard to preserve.**
