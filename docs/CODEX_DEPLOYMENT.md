# Codex Local Deployment SOP

## Goal

A clone or ZIP of this repository should let Codex turn a Windows/Linux/macOS machine into an AERIS local development/runtime workspace without writing to the canonical core repository.

## Codex sequence

1. Read `AGENTS.md`.
2. Confirm current repo is `0_JN1_AERIS_Local-computer-implementation`.
3. Run the platform installer.
4. Run tests.
5. Run `doctor`.
6. If online, synchronize the core reference read-only.
7. Select runtime mode.
8. Implement/test locally.
9. Never write to `Space653000/0_JN1_AERIS`.

## Windows bootstrap

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

If the machine must be initialized while disconnected and the core reference cannot be refreshed:

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1 -SkipCoreSync
```

## Runtime mode switching

```powershell
.\scripts\run.ps1 mode show
.\scripts\run.ps1 mode offline
```

Correction: setting a mode uses the explicit `set` subcommand:

```powershell
.\scripts\run.ps1 mode set offline
.\scripts\run.ps1 mode set local
.\scripts\run.ps1 mode set cloud
.\scripts\run.ps1 mode set auto
```

## Minimum verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\scripts\run.ps1 doctor
```

Expected policy outcomes:

- `offline` always routes to local provider;
- `local` always routes to local provider;
- `cloud` uses configured cloud provider and may fall back to local;
- `auto` prefers local and uses cloud only when local is unavailable;
- the core cached clone has a disabled push URL and deny pre-push hook.

## Cloud credential rule

Codex may tell the Human which `.env` variables are missing. Codex must not invent, print, commit, or exfiltrate secrets.

## Local model rule

Codex may detect a local provider and model; it must not claim offline readiness if no local inference runtime/model is actually reachable.

## Delivery report template

```text
Core target repo: Space653000/0_JN1_AERIS
Core target SHA: ...
Core remote write performed: NO
Implementation workspace: ...
Runtime mode tested: ...
Local provider: READY / UNAVAILABLE
Cloud provider: CONFIGURED / NOT_CONFIGURED
Unit tests: PASS / FAIL
Doctor: READY / READY_WITH_LIMITS / BLOCKED
Offline test: PASS / FAIL
Changed local files: ...
Remaining risks: ...
```
