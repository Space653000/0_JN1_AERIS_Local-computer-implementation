# AERIS Unattended Local Operations

## User experience target

After Codex receives the two canonical GitHub repositories plus the Human-selected local path, `AERIS_AUTOPILOT` must perform every safe detectable action automatically. The Human is interrupted only by a genuine permission, license, secret, physical hardware/calibration, Core-policy, or formal R3/R4 release gate.

## What Autopilot now attempts automatically

```text
install / update
→ Core guard + alignment
→ machine/model/knowledge setup
→ deterministic tests
→ real-machine acceptance
→ company opening
→ loopback Dashboard / API
→ unattended persistence registration
→ watchdog continuity
→ Evidence / Audit handoff
```

## Windows

Default persistence is a **current-user Scheduled Task at logon** running:

```text
<venv-python> -m aeris_runtime.watchdog --port 8765 --interval 20
```

The Scheduled Task is configured with `RestartCount`/`RestartInterval` and `IgnoreNew` multiple-instance policy. If local OS policy prevents Scheduled Tasks, AERIS installs a current-user Startup-folder fallback and records `REGISTERED_WITH_LIMITS`.

This is deliberately **not claimed as a pre-login SYSTEM Windows Service**. Many local AI runtimes, licenses and user secrets are user-scoped. If the Human specifically requires headless operation before any user logs in, that becomes a machine-specific admin/service-account gate and must be separately verified.

## Linux / Jetson

Preferred persistence is a `systemd --user` service with `Restart=always`. If the user systemd manager is unavailable, AERIS may fall back to a reboot cron wrapper and records `REGISTERED_WITH_LIMITS`.

Headless pre-login operation may require user lingering or system-level service configuration. That is a real OS-policy/admin gate, not something AERIS should fake.

## Self-healing scope

The watchdog may restart only the local loopback supervisor. It **must not** bypass:

- invalid/unverified Core cache;
- failed real-machine acceptance;
- privacy endpoint policy;
- missing local model required by the active mode;
- R3/R4 Human approval;
- proprietary license/hardware/calibration gates.

A failed restart is recorded as `BLOCKED_OR_FAILED` in:

```text
.aeris/state/UNATTENDED_OPERATIONS.json
```

Persistence installation evidence is stored in:

```text
.aeris/state/UNATTENDED_INSTALL.json
```

## Independent review

Claude Code reads the persistence/runtime reports and the live loopback health endpoint. Missing or fallback-only persistence can only produce a limitation; a blocked persistence or failed watchdog recovery is a review failure.

## What still requires the actual local machine

GitHub CI can test code, script syntax and non-mutating persistence smoke. It cannot truthfully prove that a particular PC's Task Scheduler, systemd, reboot behavior, login policy, Ollama process, GPU driver, proprietary license or physical instrument survives a real restart.

Therefore the **only final local verification that cannot be replaced by GitHub** is:

1. run real `AERIS_AUTOPILOT` once;
2. confirm `UNATTENDED_INSTALL.json` is registered/accepted;
3. reboot or sign out/in once;
4. confirm `http://127.0.0.1:8765/` returns and `UNATTENDED_OPERATIONS.json` is `HEALTHY`/`RECOVERED`;
5. run `CLAUDE_VERIFY_AERIS` for independent evidence.

That single real-machine cycle replaces repeated exploratory Codex runs.
