# AERIS Local Runtime Architecture

## Purpose

This repository is the executable realization of the read-only AERIS Core target. It is **not** an alternate product definition.

```text
READ-ONLY CORE SSOT
Space653000/0_JN1_AERIS@main
        │
        │ fetch / inspect / compare only
        ▼
LOCAL IMPLEMENTATION REPO
Space653000/0_JN1_AERIS_Local-computer-implementation
        │
        │ branch → tests → PR → main
        ▼
SUPPORTED / PROFILE-MATCHED LOCAL COMPUTER
        │
        │ real-machine acceptance
        ▼
VERIFIED SCOPE-SPECIFIC AERIS INSTANCE
```

The architectural center remains:

```text
1 Human Chief Engineer
+ 100 capability seats (not 100 persistent agents)
+ ordinary pod 2–8 / complex pod 5–15
+ model-neutral orchestration
+ Skills / Methods / Standards / Workflows
+ real engineering tools
+ Evidence / Provenance
+ Independent Verification
+ Human Approval
+ Reproducibility
```

Deployment/security maturity must never substitute for those Core engineering-trust capabilities.

## Runtime planes

### 1. Reference Plane

`.aeris/core-reference` is a local read-only representation of `0_JN1_AERIS/main`.

Guarded Git cache requirements:

- fetch URL must be the canonical Core repository;
- push URL disabled;
- deny `pre-push` hook present;
- detached HEAD;
- HEAD == `origin/main` == recorded `core-target.json` SHA;
- working tree clean.

Air-gap snapshot requirements:

- canonical Core SHA recorded;
- exact file inventory;
- per-file SHA-256;
- extra/missing/changed files rejected.

Important: an unsigned snapshot hash manifest proves integrity **relative to the manifest you trust**; it does not by itself prove source authenticity. Production/high-assurance relocation still needs a trusted signing/attestation policy.

### 2. Model Plane

Models are replaceable compute, not AERIS identity.

Private engineering routing is invariant across modes:

```text
PRIVATE ENGINEERING
        ↓
endpoint policy
        ↓
loopback (default)
OR explicit trusted_lan literal private IP
        ↓
LOCAL AI
```

A public/global endpoint can never be treated as the private local provider merely because it was configured as `AERIS_LOCAL_BASE_URL`.

Public research is a separate channel:

```text
PUBLIC RESEARCH
  offline/local → local provider
  cloud         → configured cloud; optional policy-controlled local fallback
  auto          → local first; cloud allowed only when local unavailable and cloud configured
```

Current provider contracts:

- `OllamaProvider`: endpoint-policy-constrained local / trusted-LAN inference;
- `OpenAICompatibleProvider`: public-research cloud baseline only.

Model-neutral architecture does not mean every AI provider is already implemented.

### 3. Local State Plane

Generated state belongs under `.aeris/` and is never committed.

Examples:

- selected runtime mode;
- cached Core target and SHA;
- machine/deployment reports;
- Knowledge DB;
- ingress quarantine;
- local acceptance evidence;
- future workflow/evidence/audit state.

### 4. Data Plane

`data/`, `memory/`, `evidence/`, `.aeris/` and logs are local/private by default. Customer-owned acoustic data must never be automatically attached to public cloud research.

## Offline definition

Offline-capable does **not** mean a clean machine can conjure missing dependencies without a network.

A verified offline workflow requires beforehand:

1. implementation source/package present;
2. verified Core cache/snapshot present;
3. compatible Python/runtime present;
4. local inference runtime already installed or supplied through a genuinely self-contained verified machine-specific package;
5. required local model weights imported;
6. intended Skills/Methods/data/tools local;
7. real offline inference and acceptance pass.

On Linux/Jetson, `ollama-install.sh` is treated as a network/bootstrap installer, **not** as a self-contained air-gap runtime package. Offline mode refuses to execute it when Ollama is absent.

## Core P0 priority

The secure portable kernel is only foundation work. The next architecture priority follows canonical Core P0:

```text
task identity / state
→ Evidence Bundle
→ Acceptance / Verification
→ Golden failure cases
→ independent review
→ audit
→ health / expected-run monitoring
→ Skills / Methods / Standards
```

Do not keep polishing deployment indefinitely while these remain absent, or AERIS would become a secure portable chatbot shell rather than an Acoustic Engineering Organization OS.

## Future expansion

- executable Skill registry and acoustic Methods;
- provenance-aware Standards Registry;
- engineering Knowledge promotion flow;
- Evidence Bundle store;
- engineering state machine;
- G0–G5 verification;
- independent reviewer / Human approval records;
- Golden acoustic regression cases;
- instrument / CAE adapters;
- local web dashboard/API backed by real truth;
- observability and reproduction runner.

The invariant is unchanged: **cloud may improve public research capability; local preserves private engineering sovereignty and continuity; evidence and verification establish engineering truth.**
