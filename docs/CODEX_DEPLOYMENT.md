# Codex Local Deployment SOP

## Goal

A clone or ZIP of this repository lets Codex help build/test an AERIS local workspace **without writing to the canonical Core repository**. It does not give Codex authority to call an unverified machine/company complete.

## Canonical boundary

```text
Space653000/0_JN1_AERIS@main
= READ-ONLY design authority

Space653000/0_JN1_AERIS_Local-computer-implementation
= writable implementation/construction repo

local machine
= actual runtime/evidence state
```

If implementation and Core disagree, Core wins. CI `scripts/check-core-drift.py` blocks silent Core drift.

## Codex sequence

1. Read `AGENTS.md`, `docs/AUDIT_REALITY_CHECK.md`, `config/maturity.json`.
2. Confirm current repo is `0_JN1_AERIS_Local-computer-implementation`.
3. Run the platform one-click installer.
4. Run unit/security tests and `company status`.
5. Verify the cached Core push URL/hook is read-only.
6. Run `doctor`.
7. Run `scripts/local-acceptance.*` on the real machine.
8. Only claim the maturity level backed by generated evidence.
9. Implement/test in the implementation repo/local workspace.
10. Never write to `Space653000/0_JN1_AERIS`.

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

If deliberately offline and a Core snapshot was staged:

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1 -SkipCoreSync
```

`-SkipLocalModelInstall` is a controlled/CI option and prevents a full local-continuity claim.

## Linux / Jetson

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

CI-only smoke may set `AERIS_SKIP_LOCAL_RUNTIME_INSTALL=1`; a real deployment must not use this shortcut if local continuity is required.

## Runtime mode semantics

```powershell
.\scripts\run.ps1 mode set offline
.\scripts\run.ps1 mode set local
.\scripts\run.ps1 mode set cloud
.\scripts\run.ps1 mode set auto
```

Truthful behavior:

- **private engineering chat is local in every mode**;
- `offline` keeps research local and blocks AERIS external URL ingress;
- `local` keeps research local but does not itself prove OS/network isolation;
- `cloud` permits cloud only for the public-research channel;
- `auto` prefers local public research and may use cloud when local is unavailable;
- DLP heuristics can block likely secrets/confidential public queries, but Human classification is still required.

## Minimum automated verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\check-core-drift.py
.\scripts\run.ps1 company status
.\scripts\run.ps1 doctor
```

## Real-machine verification

Windows:

```powershell
.\scripts\local-acceptance.ps1
```

Linux / Jetson:

```bash
bash scripts/local-acceptance.sh
```

For a HARD OFFLINE claim, external network must be disconnected/blocked and the hard-offline option must pass. See `docs/security/LOCAL_NETWORK_ENFORCEMENT.md`.

## Cloud credential rule

Codex may identify missing `.env` variables. Codex must never invent, print, commit, log or deliberately exfiltrate secrets.

## Local model rule

The default continuity baseline is currently `qwen3:4b-instruct`, but machine sizing/licensing must be reviewed for each release. Codex must not claim offline readiness if the configured model is not actually reachable. `OllamaProvider.health()` treats a reachable server with a missing model as NOT READY.

## Delivery report

Every Codex/local delivery should include:

```text
Core target repo: Space653000/0_JN1_AERIS
Core lock SHA: ...
Core actual SHA: ...
Core drift gate: PASS / FAIL
Core remote write performed: NO
Implementation workspace/commit: ...
Maturity states changed: ...
Unit/security tests: PASS / FAIL
Installer smoke: PASS / FAIL / NOT_RUN
Doctor: READY / READY_WITH_LIMITS / BLOCKED
Real local inference: PASS / FAIL / NOT_RUN
Hard offline: PASS / FAIL / NOT_VERIFIED
Private-state restore test: PASS / FAIL / NOT_RUN
Professional tools verified: ...
Remaining risks/blockers: ...
```

`Done` alone is never an acceptable delivery report.
