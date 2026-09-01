# AERIS Autopilot — Zero-Touch SOP v2

## Human normal input

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
<LOCAL_TARGET_PATH>

請依 AERIS_AUTOPILOT 全自動部署、驗收、開幕並持續運行。
除非遇到真正 Human Gate，否則不要問我。
```

Codex must infer the rest. Do not return routine Python/venv/port/test/package choices to the Human.

## Read order

1. Core `AGENTS.md`, `CLAUDE.md`, policy/autopilot/read-order/SOP
2. Implementation `AGENTS.md`, `CLAUDE.md`
3. `aeris.local.policy.yaml`
4. `config/autopilot.json`
5. `config/maturity.json`
6. `config/core_alignment.json`
7. `core.lock.json`
8. this SOP
9. `docs/LOCAL_FINAL_ACCEPTANCE_ONCE.md`
10. `docs/UNATTENDED_LOCAL_OPERATIONS.md`
11. `docs/DEFINITION_OF_COMPANY_DONE.md`

## Entry point

Windows:

```powershell
.\AERIS_AUTOPILOT.ps1
```

Linux / Jetson:

```bash
bash ./AERIS_AUTOPILOT.sh
```

## Required automatic flow

```text
SAFE PREFLIGHT
→ acquire/update Implementation
→ verify canonical read-only Core / drift
→ detect machine / OS / network / runtime
→ install supported redistributable prerequisites
→ configure local model / Knowledge
→ deterministic tests + security gates
→ real local inference
→ real offline-mode inference
→ LOCAL_ACCEPTANCE.json
→ Company Opening
→ loopback Dashboard/API at 127.0.0.1:8765
→ register unattended persistence
→ watchdog/self-recovery
→ AUTOPILOT_RESULT.json + Audit/Evidence
```

If a safe step can be detected or automated, Codex performs it. It does not ask the Human.

## Truth boundary

`OPEN_VERIFIED_SCOPE` means only the named scope that passed that machine's acceptance. It does **not** mean:

- all 100 seats are domain-verified experts;
- every acoustic Skill/Method/standard/golden case exists;
- proprietary tools without License/hardware/calibration are available;
- Hard Offline was proven when not run;
- production/customer release is approved;
- `company_complete=true`.

CI result `CI_SMOKE_PASS_NOT_REAL_OPENING` is never real-machine evidence.

## Unattended operation

After successful local acceptance/opening, Autopilot attempts automatically:

- Windows: current-user Scheduled Task with restart policy; Startup-folder fallback if policy blocks it.
- Linux/Jetson: `systemd --user` with `Restart=always`; cron wrapper fallback if needed.
- Watchdog: restarts only the loopback Supervisor and never bypasses Core/privacy/acceptance/Human gates.

Default persistence is user-session/logon scope. A pre-login SYSTEM/root service is not claimed automatically because local model/runtime/license/secret availability can be user-scoped.

Evidence:

```text
.aeris/state/UNATTENDED_INSTALL.json
.aeris/state/UNATTENDED_OPERATIONS.json
```

## Human gates only

Stop only for the minimum exact action when blocked by:

- denied admin/OS persistence policy or required pre-login service;
- License/EULA;
- secret/customer credential/hardware token;
- physical cable/fixture/chamber/instrument/calibration;
- destructive unrelated disk/network/firewall impact;
- Core policy change;
- the one-time reboot/logoff needed to prove persistence;
- R3/R4 production/customer/formal release.

## One local cycle only

GitHub CI must catch software/syntax/API/workflow defects first. Do not burn local Codex Token repeating cloud-reproducible tests.

The final local cycle is defined only in:

`docs/LOCAL_FINAL_ACCEPTANCE_ONCE.md`

After it completes, Claude Code runs the independent acceptance entrypoint when installed/authorized:

```text
Windows: .\CLAUDE_VERIFY_AERIS.ps1
Linux/Jetson: bash ./CLAUDE_VERIFY_AERIS.sh
```

If Claude/account authorization is unavailable, record `NOT_RUN`; never invent an independent PASS.

## Evidence over prose

Final status is determined from Core/Implementation SHA, machine profile, tests, Core integrity, local/offline inference, opening, persistence/watchdog, Audit/Evidence, Claude review and explicit remaining blockers—not from an AI saying “完成”.
