# AERIS FULL BUILD Autopilot — Zero-Touch SOP

## Human normal input

If Codex already has one explicit/active safe writable workspace, the Human only needs to paste:

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
```

Those two URLs mean: **run AERIS FULL BUILD AUTOPILOT now**.

Do not ask for another prompt. Do not ask `確認執行`. If a path is supplied, use it. Otherwise use the one selected/active safe workspace. Ask only when no safe target exists or multiple targets are genuinely ambiguous.

## Automatic lifecycle

```text
latest CI-passed Implementation main
→ read-only Core alignment
→ GAP INVENTORY
→ SOFTWARE GAP CLOSURE LOOP
→ machine inventory
→ install/configure supported prerequisites
→ local model + Knowledge
→ deterministic/security tests
→ real Local + Offline inference
→ Company Opening
→ 127.0.0.1:8765 Dashboard/frontend/backend
→ OS-native unattended persistence
→ watchdog/self-recovery
→ Evidence/Audit
```

Windows entrypoint: `./AERIS_AUTOPILOT.ps1`  
Linux/Jetson: `bash ./AERIS_AUTOPILOT.sh`

## Software Gap Closure Loop

Before final opening, Codex must inventory `config/maturity.json`, `docs/DEFINITION_OF_COMPANY_DONE.md`, canonical Core requirements, UI/API/workflows, Skills/Methods/Standards, trust primitives, health/reproduction and tests.

For every missing capability:

```text
software-only + safe + not external/Human blocked
→ implement automatically
→ add/update deterministic tests
→ run tests
→ continue

License/hardware/secret/physical/Human dependency
→ preserve exact blocker/evidence
→ Human Gate
```

`NOT_IMPLEMENTED` is not a valid stopping reason when Codex can safely implement the missing software. The run continues until no safe software-only gap remains or the next gap is a genuine Human/external gate.

The two-URL trigger is standing authorization for reversible R0/R1 software work and controlled R2 work whose safety preconditions are satisfied. No separate large-task plan confirmation is required.

## Token efficiency

Use the latest Windows+Ubuntu CI-passed GitHub `main`. Catch cloud-reproducible software bugs in GitHub/CI before spending local Codex Token. Local execution is primarily for machine-specific install/runtime/inference/persistence/reboot evidence and defects that genuinely require that machine.

Do not launch Claude Code or another model reviewer by default. Do not use Codex Tasks/scheduling for continuity.

## Continuous operation

AERIS continuity must not depend on Codex staying open:

- Windows: current-user Scheduled Task with restart policy; Startup fallback when policy blocks ScheduledTasks.
- Linux/Jetson: systemd user service with `Restart=always`; cron wrapper fallback.
- Watchdog restores the loopback Supervisor without bypassing Core/privacy/Human gates.

## Human Gates only

Stop only for the minimum exact action when blocked by: no safe/unambiguous target, OS/admin/persistence policy, License/EULA, secret/token, physical fixture/calibration, destructive unrelated system change, Core policy change, one-time reboot/logoff acceptance, or R3/R4 formal release.

After the Human performs that one action, resume automatically from preserved state.

## Truth boundary

FULL BUILD requires every safely implementable software-only gap to be closed before final opening. It does not authorize fake success for unavailable licenses, hardware, calibration, credentials, Hard Offline evidence not actually tested, or production/customer approval.

Optional Claude/reviewer tooling remains available only if the Human explicitly requests it.

**The Human should not need to remember an orchestration prompt. The two canonical GitHub URLs are the orchestration prompt.**
