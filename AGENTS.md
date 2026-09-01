# AGENTS.md — AERIS Local Company Autopilot Contract

Repository: `Space653000/0_JN1_AERIS_Local-computer-implementation`  
Canonical read-only target: `Space653000/0_JN1_AERIS@main`

## 0. Human + AI operating model

```text
Human Chief Engineer = final authority
Canonical Core       = read-only design authority
Codex                = primary local executor / installer / implementer
Claude Code          = independent reviewer / acceptance auditor
Evidence             = decision basis
```

Model/agent agreement is not engineering evidence.

## 1. Automatic deployment trigger

If the Human supplies:

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
<LOCAL_TARGET_PATH>
```

Codex must interpret it as an `AERIS_AUTOPILOT_REQUEST` and continue automatically without asking routine optional setup questions.

### Required sequence

1. read Core `AGENTS.md`, `CLAUDE.md`, `aeris.policy.yaml`, `aeris.autopilot.json`, canonical read-order/SOP;
2. acquire/update this Implementation at `<LOCAL_TARGET_PATH>` without overwriting unrelated data;
3. read this `AGENTS.md`, `CLAUDE.md`, `aeris.local.policy.yaml`, `config/autopilot.json`, `config/maturity.json`, `config/core_alignment.json`, `core.lock.json`;
4. verify Core drift/alignment before accepting a changed Core baseline;
5. invoke the platform entrypoint:
   - Windows: `./AERIS_AUTOPILOT.ps1`
   - Linux/Jetson: `bash ./AERIS_AUTOPILOT.sh`
6. let Autopilot detect/inventory/install/configure/test/accept/open/start local supervisor;
7. inspect generated reports rather than trusting command prose;
8. stop only at a genuine Human gate;
9. after Codex finishes, hand the same path to Claude Code for independent `CLAUDE_VERIFY_AERIS` acceptance.

Codex should not make the Human choose Python paths, virtualenv commands, package order, default local port, log directories, routine test commands or other safely detectable implementation details.

## 2. Core authority boundary

`Space653000/0_JN1_AERIS@main` is highest design authority.

Normal Codex deployment may read/clone/fetch/compare Core but MUST NOT push, PR, merge, update files/refs/settings/Rulesets or auto-accept Core drift.

If Core main moves beyond `core.lock.json`, fail closed. The new Core semantics must be deliberately reviewed before lock/alignment is updated.

## 3. Implementation remote boundary

For **normal local deployment**, GitHub Implementation is also a source image, not a place to mutate merely because installation needs adaptation. Machine-specific state belongs under `.aeris/`, `data/`, `logs/`, `.env` or other documented local/generated locations.

If the Human explicitly requests implementation development, use branch → tests → PR → protected `main`. Do not mix development publication with a deployment run.

## 4. Exact implementation read order

1. `AGENTS.md`
2. `CLAUDE.md`
3. `aeris.local.policy.yaml`
4. `config/autopilot.json`
5. `config/maturity.json`
6. `config/core_alignment.json`
7. `core.lock.json`
8. `docs/AUTOPILOT_ZERO_TOUCH_SOP.md`
9. `docs/LOCAL_VERIFICATION_SOP.md`
10. `docs/AUDIT_REALITY_CHECK.md`
11. `docs/DEFINITION_OF_COMPANY_DONE.md`
12. task-specific code/tests/Skills/Methods/Standards/adapters.

## 5. Autopilot truth boundary

Autopilot may truthfully produce:

```text
BLOCKED
OPEN_WITH_LIMITS
OPEN_VERIFIED_SCOPE
```

`OPEN_VERIFIED_SCOPE` means only the exact named local kernel scope that passed real-machine acceptance. It never means:

- all 100 seats are mature autonomous engineers;
- all Skills/Methods/Standards exist;
- all professional tools are integrated;
- Hard Offline was proven when not tested;
- production/customer release is approved;
- Company Complete.

CI uses an explicit smoke path. `CI_SMOKE_PASS_NOT_REAL_OPENING` must never be promoted into real-machine evidence.

## 6. Human gates — ask only when genuinely blocked

Codex should continue automatically until one of these occurs:

- OS elevation/admin is denied;
- proprietary license/EULA requires Human acceptance;
- secret/customer credential/hardware token is required;
- physical cable/fixture/chamber/instrument/calibration action is required;
- destructive disk/network/firewall action could affect unrelated systems;
- Core policy itself needs changing;
- production/customer/formal/external release approval is required.

When blocked, preserve all completed evidence and request the **minimum exact Human action** needed to resume.

## 7. No destructive convenience

Autopilot/deployment must be idempotent and conservative:

- never wipe an unrelated non-empty target directory;
- never delete customer/private data to repair setup;
- never silently commit secrets or private data;
- never weaken privacy/checksum/signature/Core/verification gates;
- never auto-accept proprietary terms;
- never invent credentials;
- prefer reuse/resume over recreation;
- a dirty tracked implementation worktree blocks zero-touch opening rather than being silently overwritten.

## 8. Privacy

Default local content = `LOCAL_ONLY`.

Private engineering is restricted to endpoint-policy-compliant loopback or explicit trusted-LAN private literal IP. Public/global endpoints cannot be mislabeled Local.

Cloud is an explicit public-research ingress channel. Local files, Memory, Evidence, customer/project data, measurement/CAE/factory data and private history must not be attached automatically.

Application privacy is not an OS-wide mathematical zero-egress proof.

## 9. Offline continuity

Offline company operation requires all necessary local runtime/model/data/Skills/tools already present. Software `mode=offline` is not itself an air gap.

Linux/Jetson `ollama-install.sh` bootstrap is not a self-contained air-gap runtime package. Missing genuine offline prerequisites must BLOCK rather than silently use network.

## 10. P0 trust primitives

The implementation must protect these before adding cosmetic automation:

- task identity + guarded state machine;
- Evidence Bundle hashes/provenance;
- G0–G5 structured gates;
- independent review;
- R0–R4 authority/Human approval;
- audit ledger;
- company opening/heartbeat truth;
- later Golden acoustic cases, reproduction, mature Skills/Methods/Standards and tool adapters.

Application hash chains/manifests are integrity baselines, not WORM storage or external cryptographic attestation.

## 11. Completion evidence

Every Codex Autopilot completion reports exact paths/values for:

```text
Core SHA
Core remote write performed: NO
Implementation SHA
Local target path
Machine Profile
Runtime mode
Private endpoint scope
Autopilot result
Unit/security tests
Core integrity
Local inference
Offline inference
Hard Offline result or NOT_TESTED
Company opening state
Supervisor/heartbeat
Audit/evidence paths
Unverified capabilities
External blockers
Minimal Human action, if any
```

## 12. Independent Claude handoff

Codex does not self-certify its own deployment. After Autopilot, Claude Code runs:

```text
Windows: ./CLAUDE_VERIFY_AERIS.ps1
Linux/Jetson: bash ./CLAUDE_VERIFY_AERIS.sh
```

Claude's default pass is review-only and must not silently repair and then approve in the same context.

## 13. No false done

`docs/DEFINITION_OF_COMPANY_DONE.md` remains the implementation completion gate. AERIS's purpose is a trustworthy Acoustic Engineering Organization OS, not a green installer demo.
