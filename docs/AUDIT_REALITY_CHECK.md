# AERIS Reality Check / Anti-Fantasy Audit

**Status date:** 2026-09-01  
**Applies to:** `Space653000/0_JN1_AERIS_Local-computer-implementation`  
**Canonical design authority:** read-only `Space653000/0_JN1_AERIS@main`

## 1. Non-negotiable truth rule

AERIS uses five implementation states:

`NOT_IMPLEMENTED → IMPLEMENTED → TESTED → VERIFIED`

External dependencies that cannot be completed inside this public repository use `BLOCKED_EXTERNAL`.

No AI, README, dashboard or installer may promote a capability by prose alone.

- `IMPLEMENTED` = code/config exists.
- `TESTED` = automated tests exercise the claimed contract.
- `VERIFIED` = required real-machine / real-tool / real-evidence acceptance has passed.
- CI green means only the checks executed by CI passed.
- A 100-seat registry means 100 capability slots are defined; it does **not** mean 100 mature engineers already exist.

Machine-readable source: `config/maturity.json`.

## 2. Current product stage

**PRE_ALPHA Portable Company Kernel.**

Currently real and testable:

- 100-seat registry count and grouping;
- local/private chat routing to Ollama-compatible local AI;
- public-research-only cloud adapter boundary;
- application-level cloud egress policy and DLP screening;
- public URL ingress with non-public-address/SSRF protection;
- SQLite local knowledge index;
- Windows/Linux CI kernel tests;
- machine detection baseline;
- one-click installer implementation and CI smoke mode;
- read-only cached Core sync mechanism;
- portable software-image packaging;
- real-machine local/offline acceptance scripts;
- encrypted private-state backup/restore mechanism using `age`.

Not yet a completed professional acoustic company:

- 100 executable role contracts;
- mature acoustic Skill library;
- deterministic Methods library;
- live standards registry with lifecycle refresh;
- Dynamic Pod engine;
- workflow execution/state engine;
- Evidence Bundle engine and append-only audit;
- G0–G5 verification engine;
- Golden acoustic datasets/regression suite;
- COMSOL/MATLAB/APx/KLIPPEL/SoundCheck/ACQUA adapters;
- live local Dashboard/Workspace/Services backend;
- OS-level DLP/network egress enforcement;
- clean-machine Windows/Linux/Jetson verification evidence;
- full-company relocation verified across machines.

## 3. Core repository write boundary

The Core repository is policy-defined read-only for Codex and local implementation. Local cached clones disable the push URL and install a deny `pre-push` hook.

This is **not equivalent to GitHub server-side branch protection**. Server-side protection/rulesets and write credential scoping must be configured by the Human on GitHub. Until that exists, maturity must not claim cryptographic/administrative immutability of Core.

## 4. Privacy claim boundary

AERIS can truthfully claim:

> AERIS application code never automatically attaches local Memory, Evidence, files or customer data to cloud research requests; private engineering chat is hard-routed to local AI.

AERIS must **not** claim:

> No process on the computer can ever leak data.

That stronger statement requires local OS/network enforcement, process controls and verification. See `docs/security/LOCAL_NETWORK_ENFORCEMENT.md`.

The `research` command is a **public channel**. DLP heuristics block obvious secrets/confidential markers, but heuristics cannot prove absence of sensitive information. Human classification remains required.

## 5. Offline claim boundary

`mode=offline` prevents AERIS model routing from using cloud and now blocks AERIS public URL ingress. A machine is not `HARD_OFFLINE_VERIFIED` until:

1. local inference runtime/model is installed;
2. real local inference succeeds;
3. external network is physically disconnected or blocked;
4. `scripts/local-acceptance.*` passes in hard-offline mode;
5. required Skills/data/tools for that workflow are local.

## 6. Model baseline

Default local continuity model is `qwen3:4b-instruct` through Ollama-compatible API. Model licensing and exact tag must be rechecked before commercial release. The model is replaceable compute, not AERIS identity and not evidence of 100-person capability.

## 7. Professional tools

COMSOL, MATLAB, APx, KLIPPEL, SoundCheck, ACQUA, Ansys and Simcenter remain external/licensed dependencies. Documentation or detection does not equal an adapter. They may only move to `VERIFIED` after legal installation, version capture, adapter implementation, tool-specific E2E test and where applicable hardware/calibration evidence.

## 8. Relocation truth

There are three different objects:

1. **Software Company Image** — public repository/package; no secrets/private state.
2. **Encrypted Private State** — `.env`, local Knowledge/Memory/Evidence/data/logs encrypted with `age`.
3. **Private Asset Pack** — model weights, proprietary installers/licenses, drivers/calibration, private datasets.

A real company move requires all applicable objects plus restore acceptance. A software ZIP alone is not a full-company relocation.

## 9. Release rule

No release may be called `COMPLETE`, `PRODUCTION READY`, `100 ENGINEERS READY`, `OFFLINE VERIFIED`, `PRIVACY GUARANTEED`, or `FULL COMPANY RELOCATABLE` unless the corresponding state in `config/maturity.json` is `VERIFIED` and the required evidence artifact exists.
