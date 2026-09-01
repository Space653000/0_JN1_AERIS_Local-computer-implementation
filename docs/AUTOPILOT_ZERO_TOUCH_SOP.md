# AERIS Autopilot — Zero-Experience Local Deployment SOP

## 0. Human input target

The normal Human input is only:

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
<LOCAL_TARGET_PATH>
```

A capable Codex environment with GitHub + terminal access should infer the Core Autopilot contract, acquire this repository at the local path and invoke the correct platform entrypoint automatically.

This is a **zero-experience operating target**, not a claim that a repository can override OS security, vendor licensing, missing credentials, physical calibration or an agent host that has not granted terminal/network privileges.

## 1. Exact read order

Before mutation:

1. Core `AGENTS.md`
2. Core `CLAUDE.md`
3. Core `aeris.policy.yaml`
4. Core `aeris.autopilot.json`
5. Core `docs/governance/AI_READ_ORDER.md`
6. Core `docs/governance/AI_AUTOPILOT_SOP.md`
7. this repository `AGENTS.md`
8. this repository `CLAUDE.md`
9. `aeris.local.policy.yaml`
10. `config/autopilot.json`
11. `config/maturity.json`
12. `config/core_alignment.json`
13. `core.lock.json`
14. this SOP
15. `docs/LOCAL_VERIFICATION_SOP.md`
16. `docs/AUDIT_REALITY_CHECK.md`
17. `docs/DEFINITION_OF_COMPANY_DONE.md`

## 2. Codex entrypoint

### Windows

```powershell
.\AERIS_AUTOPILOT.ps1
```

Optional explicit mode/model:

```powershell
.\AERIS_AUTOPILOT.ps1 -Mode auto -LocalModel qwen3:4b-instruct
```

Hard-offline acceptance, only after physical/network isolation and local assets exist:

```powershell
.\AERIS_AUTOPILOT.ps1 -Mode offline -HardOffline
```

### Linux / Jetson

```bash
bash ./AERIS_AUTOPILOT.sh
```

Optional:

```bash
bash ./AERIS_AUTOPILOT.sh auto --model qwen3:4b-instruct
```

Hard offline:

```bash
bash ./AERIS_AUTOPILOT.sh offline --hard-offline
```

## 3. What Autopilot actually does

```text
SAFE_PREFLIGHT
→ verify implementation origin / clean tracked source
→ record preflight

INSTALL_CONFIGURE
→ reuse existing hardened one-click installer
→ Python/venv where supported
→ Core guarded cache/snapshot
→ local inference runtime/model where supported
→ local state / Knowledge
→ unit/security tests / doctor

P0_TRUST_BASELINE
→ verify application audit ledger
→ task/evidence/verification/authority primitives available

REAL_MACHINE_ACCEPTANCE
→ supported Machine Profile
→ Core cache integrity
→ real local inference
→ real offline-mode inference
→ optional Hard Offline probes
→ LOCAL_ACCEPTANCE.json

COMPANY_OPENING
→ assess blockers/limits
→ only real acceptance can reach OPEN_VERIFIED_SCOPE
→ write COMPANY_OPENING.json

LOCAL_SUPERVISOR
→ loopback 127.0.0.1 only
→ /health = supervisor liveness + company opening state
→ /status = opening report
→ heartbeat evidence

EVIDENCE_HANDOFF
→ AUTOPILOT_RESULT.json
→ exact hashes/paths/limitations
```

The local supervisor is deliberately not a public web service. It does not bind `0.0.0.0`, and its heartbeat is **not** whole-company health proof.

## 4. Output files

```text
.aeris/state/AUTOPILOT_PREFLIGHT.json
.aeris/state/AUTOPILOT_RESULT.json
.aeris/state/DEPLOYMENT_REPORT.json
.aeris/state/LOCAL_ACCEPTANCE.json
.aeris/state/COMPANY_OPENING.json
.aeris/state/HEARTBEAT.json
.aeris/state/SUPERVISOR.json
.aeris/audit/audit.jsonl
```

Later engineering work can add:

```text
.aeris/tasks/<task_id>/task.json
.aeris/evidence/<run_id>/...
.aeris/verification/<task_id>/gates.json
```

## 5. Opening states

```text
CLOSED
BOOTSTRAPPING
BLOCKED
OPEN_WITH_LIMITS
OPEN_VERIFIED_SCOPE
```

### `OPEN_VERIFIED_SCOPE`

Currently means the exact named scope:

```text
LOCAL_PORTABLE_COMPANY_KERNEL_BASELINE
```

and only after real-machine acceptance PASS.

It does **not** mean:

- 100 mature autonomous acoustic engineers;
- complete Skills/Methods/Standards;
- complete Dynamic Pod orchestration;
- all professional tools integrated;
- production/customer/formal release approved;
- Hard Offline verified unless that probe was actually run;
- Company Complete.

Those remain visible in `config/maturity.json` and opening limitations.

## 6. CI smoke is deliberately weaker

Repository CI uses:

Windows:

```powershell
.\AERIS_AUTOPILOT.ps1 -CISmoke
```

Linux:

```bash
bash ./AERIS_AUTOPILOT.sh --ci-smoke
```

This may install/create the isolated Python environment and run repository contracts while deliberately skipping external local-AI installation/Core cache setup.

Its only legitimate result is:

```text
CI_SMOKE_PASS_NOT_REAL_OPENING
```

Never use CI smoke as real-machine or company-opening evidence.

## 7. Genuine Human gates

Autopilot should not stop for routine configuration choices. It should stop when automation would violate authority or lacks real-world input, such as:

- OS refuses required elevation;
- vendor EULA/license requires Human acceptance;
- API key/customer credential/hardware token is needed;
- cable/fixture/chamber/instrument/calibration action is physical;
- broad firewall/storage/network change may affect unrelated systems;
- canonical Core policy must change;
- customer/production/formal/external release requires Human approval.

When blocked, `AUTOPILOT_RESULT.json` preserves the stage and failure. Codex asks for one minimal next Human action, then reruns idempotently.

## 8. Dirty local source is blocked, not hidden

Zero-touch deployment refuses a dirty **tracked** implementation worktree. It will not silently reset, commit or overwrite unknown changes.

Generated/private state belongs outside tracked source, e.g.:

```text
.aeris/
.env
data/
logs/
```

If the Human explicitly requested implementation development, do that in a separate branch/CI/PR phase before running deployment from a reproducible source state.

## 9. Claude independent acceptance

After Codex Autopilot completes, Claude Code runs **without installing or repairing by default**.

### Windows

```powershell
.\CLAUDE_VERIFY_AERIS.ps1
```

### Linux / Jetson

```bash
bash ./CLAUDE_VERIFY_AERIS.sh
```

Claude generates:

```text
.aeris/state/CLAUDE_TESTS.json
.aeris/state/claude-unit-tests.log
.aeris/state/claude-core-drift.log
.aeris/state/claude-review.log
.aeris/state/CLAUDE_ACCEPTANCE.json
```

Claude checks repository tests, live remote Core drift when possible, local Core integrity, audit integrity, real-machine acceptance, opening state, supervisor and source cleanliness.

If the machine is offline and live GitHub Core comparison cannot run:

```text
remote_core_drift_gate = NOT_TESTED
```

That limitation must survive into the final review.

## 10. Repair separation

Claude acceptance must not do:

```text
find defect
→ silently repair it
→ approve its own repair
```

Required flow:

```text
review FAIL/BLOCKED
→ evidence
→ separate authorized repair
→ new/fresh independent review
```

Codex also does not self-certify its own deployment.

## 11. R0–R4 authority

Machine-readable policy: `config/risk_authority.json`.

```text
R0 read-only low-risk
R1 reversible local change + tests
R2 controlled execution + preconditions + independent review
R3 high-impact/destructive + independent review + Human approval
R4 customer/formal/production/Core publication + independent review + Human approval
```

AI cannot self-authorize R3/R4. G5 PASS requires `Human Chief Engineer` authority and evidence reference.

## 12. P0 engineering trust baseline now available

The repository contains baseline primitives for:

- task identity/state machine;
- Evidence Bundle creation/sealing/hash verification;
- G0–G5 structured gate records;
- R0–R4 authority decisions;
- application hash-chained audit ledger;
- scope-bound opening/heartbeat;
- deterministic Claude acceptance aggregation.

These are **baseline mechanisms**, not mature domain completion. In particular:

- audit hash chain is not WORM storage;
- Evidence Bundle hashes are not external signing/attestation;
- structured G0–G5 records are not yet the full acoustic-domain verification engine;
- independent reviewer allocation engine is still separate future work;
- Golden acoustic datasets, mature Skills/Methods/Standards and professional adapters remain future/externally gated work.

## 13. Normal company operation after opening

A healthy supervisor process only means the local supervisor is serving. To see scoped state:

```bash
python -m aeris_runtime company supervisor-status
python -m aeris_runtime company status
python -m aeris_runtime doctor
python -m aeris_runtime audit verify
```

Private engineering:

```bash
python -m aeris_runtime chat "..."
```

Public research uses the separate explicit public channel:

```bash
python -m aeris_runtime research "public question only"
```

Engineering work should create a task and Evidence rather than treating chat text as completion:

```bash
python -m aeris_runtime task create "<engineering objective>" --actor Codex --risk R1
python -m aeris_runtime evidence create <task_id> --actor Codex
```

## 14. What the repository cannot guarantee by itself

Even perfect repository logic cannot force every external Codex/Claude host to grant:

- terminal access;
- network access;
- OS admin rights;
- permission to install software;
- vendor license rights;
- physical access to instruments;
- secrets/credentials.

Therefore the correct promise is:

> With the required agent permissions and supported/redistributable prerequisites, AERIS Autopilot automatically performs every safe deterministic step and stops only at a genuine Human/external gate, preserving exact evidence for resumption and independent review.

That is the maximum reliable automation boundary without turning missing authority into fiction.
