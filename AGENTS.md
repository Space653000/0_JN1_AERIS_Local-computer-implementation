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

Codex must interpret it as an `AERIS_AUTOPILOT_REQUEST` and continue automatically without asking routine setup questions.

### Required sequence

1. read Core canonical read-order/SOP and verify Core is read-only;
2. acquire/update this Implementation at `<LOCAL_TARGET_PATH>` without overwriting unrelated/private data;
3. read this repository in the exact order below;
4. run the platform `AERIS_AUTOPILOT` entrypoint;
5. let Autopilot detect/inventory/install/configure/test/accept/open the company control plane;
6. register unattended user-session persistence/watchdog when allowed by OS policy;
7. inspect generated Evidence instead of trusting command prose;
8. stop only at a genuine Human gate;
9. after the single required real-machine persistence/reboot cycle, run the Claude independent acceptance path when Claude Code is available/authorized.

Codex must not make the Human choose Python paths, virtualenv commands, package order, local ports, log locations or routine tests.

### No local-token-waste rule

Before using local Codex for exploratory repair, first verify the local checkout is synchronized to the latest GitHub `main` whose Windows + Ubuntu CI passed. Do not repeatedly rediscover GitHub-detectable software defects on the Human's machine.

The normal local strategy is **one real-machine acceptance cycle** defined in `docs/LOCAL_FINAL_ACCEPTANCE_ONCE.md`. Repeat local cycles only when the previous real-machine Evidence identifies a defect that cannot be reproduced/fixed in GitHub CI.

## 2. Core authority boundary

`Space653000/0_JN1_AERIS@main` is highest design authority.

Normal Codex deployment may read/clone/fetch/compare Core but MUST NOT push, PR, merge, update files/refs/settings/Rulesets or auto-accept Core drift.

If Core main moves beyond `core.lock.json`, fail closed. The new Core semantics must be deliberately reviewed before lock/alignment is updated.

## 3. Implementation remote boundary

For normal local deployment, GitHub Implementation is a source image, not a place to mutate merely because installation needs adaptation. Machine-specific state belongs under `.aeris/`, `data/`, `logs/`, `.env` or other documented generated/private locations.

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
9. `docs/LOCAL_FINAL_ACCEPTANCE_ONCE.md`
10. `docs/LOCAL_VERIFICATION_SOP.md`
11. `docs/UNATTENDED_LOCAL_OPERATIONS.md`
12. `docs/AUDIT_REALITY_CHECK.md`
13. `docs/DEFINITION_OF_COMPANY_DONE.md`
14. task-specific code/tests/Skills/Methods/Standards/adapters.

Earlier authority wins over later convenience documentation.

## 5. Autopilot truth boundary

Autopilot may truthfully produce:

```text
BLOCKED
OPEN_WITH_LIMITS
OPEN_VERIFIED_SCOPE
```

`OPEN_VERIFIED_SCOPE` means only the exact named local scope that passed real-machine acceptance. It never means all 100 seats are domain-verified experts, all Skills/Methods/Standards exist, all proprietary tools are integrated, Hard Offline was proven when untested, production release is approved, or Company Complete.

CI uses explicit smoke paths. `CI_SMOKE_PASS_NOT_REAL_OPENING` must never become real-machine evidence.

## 6. Human gates — ask only when genuinely blocked

Codex continues automatically until one of these occurs:

- OS elevation/admin or required persistence registration is denied;
- headless/pre-login service is required but user-session persistence is insufficient;
- proprietary license/EULA requires Human acceptance;
- secret/customer credential/hardware token is required;
- physical cable/fixture/chamber/instrument/calibration action is required;
- destructive disk/network/firewall action could affect unrelated systems;
- Core policy itself needs changing;
- system reboot/logoff needed for the one-time persistence acceptance;
- production/customer/formal/external release approval is required.

When blocked, preserve all completed Evidence and request the minimum exact Human action needed to resume.

## 7. No destructive convenience

Autopilot/deployment must be idempotent and conservative: never wipe unrelated data, delete private data to repair, commit secrets, weaken privacy/Core/verification gates, auto-accept proprietary terms, invent credentials, or silently overwrite a dirty tracked worktree.

## 8. Privacy

Default local content = `LOCAL_ONLY`.

Private engineering is restricted to endpoint-policy-compliant loopback or explicit trusted-LAN private literal IP. Public/global endpoints cannot be mislabeled Local.

Cloud is an explicit public-research ingress channel. Local files, Memory, Evidence, customer/project data, measurement/CAE/factory data and private history must not be attached automatically.

Application privacy is not an OS-wide mathematical zero-egress proof.

## 9. Offline continuity

Offline company operation requires necessary local runtime/model/data/Skills/tools already present. Software `mode=offline` is not itself an air gap.

Linux/Jetson `ollama-install.sh` bootstrap is not a self-contained air-gap runtime package. Missing genuine offline prerequisites must BLOCK rather than silently use network.

## 10. P0 trust primitives

Protect before cosmetic automation:

- task identity + guarded state machine;
- Evidence Bundle hashes/provenance;
- G0–G5 gates;
- independent review;
- R0–R4 authority/Human approval;
- audit ledger;
- expected-run health;
- reproduction;
- company opening/heartbeat/watchdog truth;
- Golden acoustic cases and mature Skills/Methods/Standards/tool adapters.

Application hash chains/manifests are integrity baselines, not WORM storage or external attestation.

## 11. Completion evidence

Every Autopilot completion reports exact Core/Implementation SHA, target path, Machine Profile, runtime/private endpoint, tests, Core integrity, local/offline inference, Hard Offline result or NOT_TESTED, opening state, persistence/watchdog, Supervisor/heartbeat, Audit/Evidence paths, unverified capabilities, external blockers and minimal Human action.

## 12. Independent Claude handoff

Codex does not self-certify its own deployment. After the real Autopilot/persistence cycle, Claude Code runs:

```text
Windows: ./CLAUDE_VERIFY_AERIS.ps1
Linux/Jetson: bash ./CLAUDE_VERIFY_AERIS.sh
```

Claude's pass is review-only: it must not silently repair and approve in the same context. If Claude CLI/account authorization is unavailable, record that independent model review is not run rather than inventing a PASS; deterministic repository review evidence may still exist separately.

## 13. No false done

`docs/DEFINITION_OF_COMPANY_DONE.md` remains the completion gate. AERIS's purpose is a trustworthy Acoustic Engineering Organization OS, not a green installer demo.
