# AERIS Autopilot — Zero-Touch SOP

## Human input

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
<LOCAL_TARGET_PATH>

請依 AERIS_AUTOPILOT 全自動部署、驗收、開幕並持續運行儀表板、前端、後端。
不要使用 Codex Tasks/排程；不要啟動 Claude Code 或其他額外模型驗收。
除非遇到真正 Human Gate，否則不要問我。
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

Stop only for denied OS privilege/policy, License/EULA, secret/token, physical fixture/calibration, destructive unrelated system change, Core policy change, one-time reboot/logoff acceptance, or R3/R4 formal release.

## Truth boundary

`OPEN_VERIFIED_SCOPE` is machine/scope-specific. It is not proof that every acoustic Skill, every one of the 100 seats, every proprietary tool, Hard Offline, or commercial release is complete. External licensed/hardware capabilities remain `BLOCKED_EXTERNAL` until real evidence exists.

Normal local deployment performs one real-machine acceptance cycle only. Optional Claude/reviewer tooling is not part of the default path and must not be launched unless the Human explicitly requests it.
