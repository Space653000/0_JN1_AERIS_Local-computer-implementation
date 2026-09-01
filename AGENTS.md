# AGENTS.md — AERIS Local FULL BUILD Autopilot Contract

Canonical Core: `Space653000/0_JN1_AERIS@main` — READ ONLY.  
Implementation: `Space653000/0_JN1_AERIS_Local-computer-implementation`.

## Human + AI authority

Human Chief Engineer = final authority. Core = design authority. Codex = default local builder/deployer/operator. Evidence = truth. Claude Code is OPTIONAL and must never launch unless the Human explicitly asks.

## Zero-prompt trigger

These two URLs are themselves the complete command when Codex already has one safe selected/active writable workspace:

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
```

Interpret them as `AERIS_FULL_BUILD_AUTOPILOT_REQUEST`.

Do not require another prompt. Do not ask `確認執行`. If the Human supplied a path, use it; otherwise use the single selected/active safe workspace. Ask for a path only if none exists or targets are genuinely ambiguous.

The two-URL trigger is standing authorization for reversible R0/R1 software work and controlled R2 work whose safety preconditions are satisfied.

## Mandatory default deployment profile

The default Full-Build path must satisfy `config/zero_cost_no_claude.v1.json` (`AERIS-ZERO-COST-NO-CLAUDE-V1`).

- Do NOT require or launch Claude Code and do NOT require a Claude token.
- Do NOT require a paid cloud API for default company opening.
- Do NOT install, purchase, activate or make default-opening dependent on paid professional software.
- Do NOT auto-accept third-party package/source/license/EULA agreements. If explicit acceptance is required, fail closed at the minimum Human Gate.
- COMSOL, MATLAB, APx, KLIPPEL, SoundCheck and ACQUA remain optional `BLOCKED_EXTERNAL` scopes until their real licensed/tool/hardware/calibration environments exist.
- Independent review is a capability-seat/authority separation rule; it is not a Claude dependency.

## Required automatic lifecycle

```text
latest CI-passed Implementation main
→ read/verify canonical Core without writing it
→ GAP INVENTORY
→ SOFTWARE GAP CLOSURE LOOP
→ machine inventory
→ install/configure supported zero-cost prerequisites
→ local model + Knowledge
→ deterministic/security tests
→ real Local + Offline inference acceptance
→ Company Opening
→ Dashboard/frontend/backend at 127.0.0.1:8765
→ OS-native unattended persistence
→ watchdog/self-recovery
→ Evidence/Audit handoff
```

## Software Gap Closure Loop

Before final opening, inspect at least:

- `config/maturity.json`;
- `config/zero_cost_no_claude.v1.json`;
- `docs/DEFINITION_OF_COMPANY_DONE.md`;
- canonical Core requirements;
- API/UI/workflows;
- Skills/Methods/Standards;
- task/evidence/G0–G5/reproduction/health;
- automated tests.

For every missing capability:

```text
software-only + safe + zero-cost + not externally blocked
→ implement automatically
→ add/update deterministic tests
→ run affected tests
→ continue

true License/paid-tool/hardware/secret/physical/Human dependency
→ preserve Evidence
→ Human/External Gate
```

Do not stop merely to report `NOT_IMPLEMENTED` when Codex can safely implement the missing software. Continue until no safe zero-cost software-only gap remains or the next gap is a genuine Human/external gate.

## AI change acceptance / regression closure

`docs/AI_CHANGE_ACCEPTANCE_PROTOCOL.md` is mandatory for every GitHub repair or implementation change.

A software defect is not closed by editing code. The required chain is:

```text
read current remote main
→ reproduce exact failure
→ add deterministic regression test/gate
→ implement fix
→ Windows + Ubuntu PR CI
→ merge only if all required jobs pass
→ verify merged main Windows + Ubuntu CI
→ only then one necessary real-machine acceptance cycle
```

If a local machine discovers a cloud-reproducible defect, convert it into a permanent GitHub regression gate before asking the Human to rerun locally. Do not silently remove or weaken a regression gate; replacement coverage and rationale must be explicit in the same PR.

Cross-file truth updates are atomic. When Core SHA changes, `core.lock.json`, `config/core_alignment.json`, `config/autopilot.json`, `company/company.manifest.json` and `config/maturity.json` must all reference the same deliberately reviewed Core SHA or CI/company validation must fail.

PR CI success is not enough to tell the Human a GitHub repair is complete. The merged `main` commit must pass its own required CI first.

## Token-efficiency rule

Use the latest GitHub `main` whose Windows + Ubuntu CI passed. Do not spend local Codex Token rediscovering cloud-reproducible defects. Prefer GitHub/CI validation before local debugging. Normal real-machine acceptance is one cycle; repeat only for genuinely machine-specific evidence/failure.

## Default execution policy

- Do NOT use Codex Tasks/scheduler for company continuity.
- Do NOT launch Claude Code, a second model reviewer or other token-consuming reviewer by default.
- Do NOT stop just to present a plan.
- Do NOT return safely detectable Python/venv/package/port/log/test choices to the Human.
- Persistence uses local OS mechanisms: Windows Scheduled Task/Startup fallback; Linux systemd-user/cron fallback; watchdog/self-recovery.

## Human Gates only

Stop only for the minimum exact action when blocked by:

- no safe/unambiguous local target;
- denied admin/OS/persistence policy;
- License/EULA/package-source agreement;
- paid professional tool required for an explicitly requested optional scope;
- secret/customer credential/hardware token;
- physical cable/fixture/chamber/instrument/calibration;
- destructive unrelated disk/network/firewall impact;
- canonical Core policy change;
- one-time reboot/logoff needed to prove persistence;
- R3/R4 production/customer/formal release.

Preserve Evidence and resume automatically afterward.

## Safety / truth

- Never push/write canonical Core during deployment/full-build.
- Never wipe unrelated/private data, invent credentials, auto-accept licenses/agreements, weaken privacy/evidence gates, or silently overwrite a dirty tracked worktree.
- Default private engineering data = `LOCAL_ONLY`.
- `OPEN_VERIFIED_SCOPE` is exact-scope evidence, not permission to fake unavailable licensed/hardware/calibration capability.
- CI PASS is not real-machine evidence; Dashboard alive is not whole-company health.

## Minimal read order

1. Core `AGENTS.md`, Core `aeris.autopilot.json`, Core Full-Build SOP.
2. This `AGENTS.md`.
3. `docs/AI_CHANGE_ACCEPTANCE_PROTOCOL.md`.
4. `config/autopilot.json`, `config/zero_cost_no_claude.v1.json`, `config/maturity.json`, `config/core_alignment.json`, `core.lock.json`.
5. `docs/AUTOPILOT_ZERO_TOUCH_SOP.md`.
6. `docs/DEFINITION_OF_COMPANY_DONE.md`.
7. Task-specific files only as needed.

Optional reviewer documents are not part of the default path.

## Entrypoints

Windows: `./AERIS_AUTOPILOT.ps1`  
Linux/Jetson: `bash ./AERIS_AUTOPILOT.sh`

Completion is determined from real capability gaps + regression gates + PR CI + post-merge main CI + `.aeris/state/*` + Audit/Evidence + actual service reachability — never from AI prose.
