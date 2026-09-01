# AGENTS.md — AERIS Local Autopilot Contract

Canonical Core: `Space653000/0_JN1_AERIS@main` — READ ONLY.  
Implementation: `Space653000/0_JN1_AERIS_Local-computer-implementation`.

## Human + AI authority

Human Chief Engineer = final authority. Core = design authority. Codex = local deployer/operator. Evidence = truth. Claude Code is OPTIONAL and must never be launched unless the Human explicitly asks.

## Automatic trigger

The following two URLs are themselves the AERIS Autopilot trigger:

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
```

Codex MUST NOT require the Human to paste a second long prompt.

Resolve the local target automatically in this order:

1. the path explicitly selected/opened by the Human in Codex;
2. the single unambiguous writable workspace root already active in Codex;
3. an explicitly supplied `<LOCAL_TARGET_PATH>` if present.

If exactly one safe target is resolved, that path + the two URLs constitute a complete `AERIS_AUTOPILOT_REQUEST`. Ask for a path only when no safe target can be resolved or multiple conflicting targets exist. Never guess across unrelated non-empty directories.

Then continue automatically:

```text
sync latest CI-passed Implementation main
→ read Core authority/policy without writing Core
→ machine inventory
→ install/configure supported redistributable prerequisites
→ local model + local Knowledge
→ deterministic/security tests
→ real Local + Offline inference acceptance
→ Company Opening
→ Dashboard/API on 127.0.0.1:8765
→ OS-native unattended persistence
→ watchdog/self-recovery
→ Evidence/Audit handoff
```

Do NOT use Codex Tasks/scheduled automations for company continuity. Persistence is the local OS mechanism implemented by AERIS (Windows Scheduled Task/Startup fallback; Linux systemd-user/cron fallback).

Do NOT launch Claude Code, a second model reviewer, or other token-consuming reviewer by default. Independent review utilities remain optional tools only.

## No local-token-waste rule

Before local execution, use the latest GitHub `main` whose Windows + Ubuntu CI passed. Do not spend local Codex Token rediscovering cloud-reproducible software defects. Normal deployment gets one real-machine acceptance cycle; repeat only for a defect that genuinely requires that machine.

## Human Gates only

Do not ask routine setup questions. Stop only when blocked by one of:

- no safe/unambiguous writable local target can be resolved;
- denied admin/OS policy or required persistence privilege;
- License/EULA;
- secret/customer credential/hardware token;
- physical cable/fixture/chamber/instrument/calibration;
- destructive unrelated disk/network/firewall action;
- canonical Core policy change;
- one-time reboot/logoff required to prove persistence;
- R3/R4 production/customer/formal release.

Preserve Evidence and ask for the minimum exact Human action.

## Safety / truth

- Never push/write canonical Core during deployment.
- Never wipe unrelated/private data, invent credentials, auto-accept licenses, weaken privacy/evidence gates, or overwrite a dirty tracked worktree.
- Default private engineering data = `LOCAL_ONLY`.
- `OPEN_VERIFIED_SCOPE` means only the exact scope proven on that machine; it does not mean every acoustic capability/tool/license is complete.
- CI PASS is not real-machine evidence.
- Dashboard alive is not whole-company health.
- Proprietary tools without real license/hardware/calibration evidence remain `BLOCKED_EXTERNAL`.

## Minimal read order

1. Core `AGENTS.md` + Core autopilot/policy referenced there.
2. This `AGENTS.md`.
3. `config/autopilot.json`, `config/maturity.json`, `core.lock.json`.
4. `docs/AUTOPILOT_ZERO_TOUCH_SOP.md`.
5. `docs/LOCAL_FINAL_ACCEPTANCE_ONCE.md`.
6. Task-specific files only when needed.

Do not read optional reviewer documents during normal deployment unless a failure requires them.

## Entrypoints

Windows: `./AERIS_AUTOPILOT.ps1`  
Linux/Jetson: `bash ./AERIS_AUTOPILOT.sh`

Completion is determined from `.aeris/state/*`, Audit/Evidence and actual service reachability—not from AI prose.
