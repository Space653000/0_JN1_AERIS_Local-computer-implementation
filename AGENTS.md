# AGENTS.md — AERIS Local Implementation Contract

Repository: `Space653000/0_JN1_AERIS_Local-computer-implementation`

Canonical read-only target:
`Space653000/0_JN1_AERIS@main`

## 1. Authority boundary

Codex may modify files in this implementation repository or its local clone.

Codex MUST NOT modify the canonical core repository `Space653000/0_JN1_AERIS`.

Forbidden against the core repository:

- push / force-push;
- create/update/delete branches or tags;
- create/update/merge PRs;
- repository contents writes;
- issue mutations for implementation delivery;
- update refs;
- Pages/settings/ruleset/protection changes;
- any GitHub write API.

The core repository is a read-only target and may only be cloned, fetched, inspected and compared.

## 2. Implementation repository purpose

This repository contains only local-execution concerns:

- model/provider adapters;
- cloud/local/offline routing;
- local orchestration/runtime;
- local deployment scripts;
- local tests and diagnostics;
- tool adapters and local services;
- local evidence/state/cache conventions.

Domain architecture, product scope and engineering North Star come from the core SSOT.

## 3. Mandatory offline invariant

No AERIS feature may make cloud connectivity a mandatory prerequisite for basic operation.

Required invariant:

```text
internet unavailable
       ↓
cloud provider unavailable
       ↓
local provider remains selectable
       ↓
AERIS local runtime still starts, diagnoses and executes supported local workflows
```

`offline` mode must never call the configured cloud provider. The local provider may run on localhost or on a Human-approved trusted LAN node.

## 4. Model independence

Do not bind AERIS identity, memory, Skills, workflows or engineering rules to a model brand.

Provider adapters are replaceable runtime implementations.

Current baseline adapters:

- local: Ollama-compatible endpoint;
- cloud: OpenAI-compatible endpoint.

New providers must implement the same provider contract rather than introducing provider-specific behavior into domain logic.

## 5. Start-of-task procedure

Before substantive code changes, Codex must:

1. confirm this is the implementation repo, not the core repo;
2. read `README.md`, this file, `core.lock.json`, and `config/runtime.json`;
3. if online, run `scripts/sync-core.*` and record the latest core SHA;
4. if offline, use the last cached `.aeris/core-reference` and/or `core.lock.json`;
5. run `python -m aeris_runtime doctor`;
6. run unit tests;
7. state which runtime mode is being targeted: offline/local/cloud/auto.

## 6. Local data and secrets

Never commit:

- `.env`;
- API keys/tokens;
- model weights;
- local engineering data;
- customer data;
- instrument credentials;
- `.aeris/` runtime/cache state;
- logs.

Use `.env.example` only as a variable template.

## 7. Completion evidence

Every Codex delivery should report:

```text
Core target repo: Space653000/0_JN1_AERIS
Core target SHA: <sha or cached sha>
Core remote write performed: NO
Implementation workspace: <path>
Runtime mode tested: <offline/local/cloud/auto>
Changed files: <list>
Tests: <result>
Doctor: <result>
Offline behavior: <result>
Cloud fallback behavior: <result if configured>
Remaining risks/blockers: <summary>
```

## 8. Packaging Definition of Done

A checkout/ZIP of this repository is deployment-ready when:

- installer succeeds without mandatory internet access after prerequisites are pre-staged;
- Python runtime has no mandatory third-party package dependencies;
- local mode works with a reachable local model server;
- offline mode blocks cloud calls;
- cloud mode can fall back to local when enabled;
- core reference can be refreshed read-only while online and reused while offline;
- unit tests pass;
- secrets and generated state remain outside Git.

## 9. Human publication boundary

Publishing implementation changes to this implementation GitHub repo is a separate Human-controlled action unless the Human explicitly asks Codex to publish here.

Even if publication is allowed here, the core `0_JN1_AERIS` repository remains read-only for Codex.