# Local AI and Model Deployment

## Baseline

Provider contract: Ollama-compatible API.  
Current default continuity model: `qwen3:4b-instruct`.

Why this baseline:

- small enough to be plausible on many local systems;
- official Ollama tag exists;
- the upstream Qwen3-4B model and Ollama tag are currently identified as Apache-2.0;
- it is a better licensing baseline than the previous `qwen2.5:3b` choice for a system that may later be used commercially.

**License status is time-sensitive. Re-check the exact model/tag/license before every commercial release. This document is not legal advice.**

## Model is not the company

A local 4B model is the continuity/retrieval/basic-reasoning layer. It does not magically provide the expertise of 100 verified acoustic engineers.

AERIS professional capability must come from the combination of:

```text
Model
+ role contract
+ verified Skills / Methods
+ local Knowledge
+ deterministic tools
+ real simulation / measurement
+ Evidence
+ independent verification
+ Human approval
```

## Sizing guideline — starting point only

- CPU / 8–16 GB: evaluate small quantized models; do not assume acceptable latency.
- 16 GB unified/VRAM class: evaluate ~4B first, then larger only after measured memory/latency/thermal tests.
- 24 GB+ GPU: larger local models may be practical, but benchmark the actual workload.
- Jetson Orin family: prefer a stable quantized model that leaves memory/thermal headroom for the rest of the application.

No machine profile may be marked `VERIFIED` from parameter count alone.

## Model assets

- Git does not store model weights.
- Online installer may use `ollama pull`.
- Air-gapped deployments must stage a legal model/runtime asset or a pre-populated model store.
- Record model identity/digest/version in the local deployment evidence when possible.

## Trusted LAN inference

A Human-approved trusted-LAN model server may remain inside the local/private security boundary if network ACLs, authentication and data-handling policy make that true. It is not automatically equivalent to public cloud.

## Acceptance

Before calling a machine local-AI ready:

1. configured local provider endpoint is reachable;
2. **configured model itself is installed**;
3. `doctor` returns READY;
4. a real `aeris chat` completes;
5. intended acoustic Knowledge/Skills are available locally;
6. latency/memory/thermal behavior is acceptable for that machine;
7. for HARD OFFLINE, external network is blocked/disconnected and local acceptance still passes.

Use `scripts/local-acceptance.*` and preserve the generated report.
