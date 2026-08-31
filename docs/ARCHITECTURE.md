# AERIS Local Runtime Architecture

## Purpose

This repository is the executable realization of the read-only AERIS core target.

```text
READ-ONLY CORE SSOT
Space653000/0_JN1_AERIS@main
        │
        │ fetch / inspect / compare
        ▼
LOCAL IMPLEMENTATION REPO
Space653000/0_JN1_AERIS_Local-computer-implementation
        │
        ├─ provider adapters
        ├─ model router
        ├─ local workflows
        ├─ tests
        ├─ deployment scripts
        └─ evidence/runtime state conventions
        │
        ▼
LOCAL COMPUTER
        │
        ├─ local model server
        ├─ cached core reference
        ├─ private data
        ├─ logs / evidence
        └─ optional cloud credentials
```

## Runtime planes

### 1. Reference Plane

`.aeris/core-reference` is a generated, read-only cached clone of `0_JN1_AERIS/main`.

- push URL is disabled;
- deny `pre-push` hook is installed;
- current fetched SHA is recorded under `.aeris/state/core-target.json`;
- when offline, the last cached version remains usable.

### 2. Model Plane

The model router is intentionally separate from AERIS identity and engineering rules.

```text
                ┌─ offline → local only; cloud denied
Task → Router ──┼─ local   → local only
                ├─ cloud   → cloud preferred → local fallback
                └─ auto    → local preferred → cloud fallback
```

Current provider contracts:

- `OllamaProvider`: localhost-oriented local inference;
- `OpenAICompatibleProvider`: configurable HTTPS cloud endpoint.

Additional providers must be adapters, not forks of AERIS domain logic.

### 3. Local State Plane

Generated state belongs under `.aeris/` and is never committed.

Examples:

- selected runtime mode;
- cached core target;
- target SHA;
- local service state;
- future workflow state/evidence indexes.

### 4. Data Plane

`data/` and `logs/` are local/private by default. Large or customer-owned acoustic data must never be committed to the public implementation repository.

## Offline definition

Offline-ready means:

1. repository source is already present;
2. Python is present;
3. local model runtime and model weights are pre-staged;
4. no cloud credential or internet is required to start the AERIS runtime;
5. `offline` mode never invokes non-loopback AI endpoints.

Cloud AI cannot itself function without a network. The system remains functional because local AI is the continuity layer.

## Future expansion

The current v0.1 intentionally keeps a narrow trustworthy kernel. Future local modules should plug into it:

- Skill registry and local acoustic methods;
- RAG / engineering memory;
- local vector/search index;
- instrument adapters;
- COMSOL / MATLAB / Python workers;
- Evidence Bundle store;
- G0–G5 verification services;
- local web dashboard and API;
- model capability routing and benchmarking.

The invariant is unchanged: cloud improves capability; local preserves sovereignty and continuity.