# AERIS Autopilot — Zero-Touch SOP

## Normal Human input

If Codex already has one explicit/active writable workspace path, the Human only needs to paste:

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
```

Those two URLs mean: **run AERIS_AUTOPILOT now**. Do not ask the Human to paste another long instruction.

Target-path resolution order:

1. Human-selected/opened Codex path;
2. single unambiguous active writable workspace root;
3. explicitly supplied `<LOCAL_TARGET_PATH>`.

Only ask for a path if none can be resolved safely or multiple conflicting targets exist.

The embedded default instruction is:

```text
Use the latest GitHub main that passed Windows + Ubuntu CI.
Run AERIS_AUTOPILOT automatically: detect, inventory, install, configure, test, Local/Offline accept, open AERIS, start Dashboard/frontend/backend, register OS-native unattended persistence and watchdog/self-recovery, and preserve Evidence/Audit.
Do not use Codex Tasks/scheduler. Do not launch Claude Code or a second model reviewer by default. Do not return safely automatable work to the Human. Stop only at a genuine Human Gate and ask for the minimum exact action needed to resume.
Never claim unimplemented or License/hardware/calibration-blocked capabilities are complete.
```

## Automatic flow

```text
latest CI-passed Implementation main
→ read-only Core alignment
→ machine inventory
→ install/configure supported prerequisites
→ local model + Knowledge
→ deterministic/security tests
→ real Local + Offline inference
→ Company Opening
→ 127.0.0.1:8765 Dashboard/API
→ OS-native unattended persistence
→ watchdog/self-recovery
→ Evidence/Audit
```

Windows entrypoint: `./AERIS_AUTOPILOT.ps1`  
Linux/Jetson: `bash ./AERIS_AUTOPILOT.sh`

## Continuous operation

AERIS continuity does not depend on Codex remaining open and does not use Codex scheduling.

- Windows: current-user Scheduled Task with restart policy; Startup fallback when policy blocks ScheduledTasks.
- Linux/Jetson: systemd user service with `Restart=always`; cron wrapper fallback.
- Watchdog restores only the local loopback Supervisor and never bypasses Core/privacy/Human gates.

## Human Gates only

Stop only for: ambiguous/no safe target path, denied OS privilege/policy, License/EULA, secret/token, physical fixture/calibration, destructive unrelated system change, Core policy change, one-time reboot/logoff acceptance, or R3/R4 formal release.

## Truth boundary

`OPEN_VERIFIED_SCOPE` is machine/scope-specific. It is not proof that every acoustic Skill, every one of the 100 seats, every proprietary tool, Hard Offline, or commercial release is complete. External licensed/hardware capabilities remain `BLOCKED_EXTERNAL` until real evidence exists.

Normal local deployment performs one real-machine acceptance cycle only. Optional Claude/reviewer tooling is not part of the default path and must not be launched unless the Human explicitly requests it.
