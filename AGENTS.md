# AGENTS.md — AERIS Portable Company Image Contract

Repository: `Space653000/0_JN1_AERIS_Local-computer-implementation`

Canonical read-only target: `Space653000/0_JN1_AERIS@main`

## 1. Repository identity

本 repository 是 **AERIS Portable Company Image**，不是只有 runtime code。

這裡應承載能讓 AERIS 搬到任意本機後重新運作的所有可版本化資產：

- company constitution / governance / organization;
- 100-seat role contracts;
- acoustic Skills / Methods / Standards / Workflows;
- model routing / agent orchestration;
- cloud/local/offline runtime;
- UI / services / tool adapters / firmware integration contracts;
- Evidence / Verification / Audit / Memory contracts;
- deployment / migration / backup / packaging;
- business operating model / service catalog / quality gates;
- tests and reproducibility assets.

## 2. Hard authority boundary

Codex MUST NOT modify `Space653000/0_JN1_AERIS`.

Against the core repo, forbidden actions include push, branch/tag mutations, PR/merge, contents writes, issue mutations used for delivery, update-ref, Pages/settings/ruleset changes, or any GitHub write API.

Core repo = read/fetch/inspect/compare only.

This implementation repo MAY be modified when the Human asks ChatGPT/Codex to build AERIS here.

## 3. Portable-company invariant

A checkout/ZIP of this repo must contain every **redistributable software/configuration/governance asset** needed to reconstruct the same AERIS company on another machine.

External/non-Git assets are allowed only when technically or legally unavoidable, e.g.:

- model weights;
- proprietary CAE / measurement software and licenses;
- customer/private datasets;
- hardware drivers that cannot be redistributed;
- credentials.

Each such dependency must have a manifest entry, preflight check and documented installation path.

## 4. Offline invariant

No essential company-control function may require cloud connectivity.

`offline` mode must never call the configured cloud provider. Local AI may be localhost or a Human-approved trusted LAN endpoint.

The system must still support company status, configuration, role/skill lookup, local workflows, evidence handling and diagnostics without internet.

## 5. Model independence

Model = replaceable compute, not AERIS identity.

Provider-specific code belongs only in adapters. Constitution, role contracts, Skills, Methods, Standards, Memory and Evidence must remain model-neutral.

## 6. Start-of-task procedure

Before substantive work:

1. confirm this is `0_JN1_AERIS_Local-computer-implementation`;
2. read `company/company.manifest.json`, `README.md`, `AGENTS.md`, `core.lock.json`, `config/runtime.json`;
3. read the relevant upstream core files read-only;
4. if online, refresh/read core target SHA without writing upstream;
5. run `python -m aeris_runtime company status`;
6. run `python -m aeris_runtime doctor`;
7. run tests;
8. state targeted runtime mode and affected company subsystem.

## 7. Completion evidence

Every delivery reports:

```text
Core target repo / SHA
Core remote write performed: NO
Portable-company repo / SHA
Subsystem changed
Runtime mode(s) tested
Company manifest validation
Tests / doctor
Offline behavior
Cloud/local routing behavior
Packaging/relocation impact
Remaining gaps
```

## 8. Company-level Definition of Done

Do not claim AERIS company is complete merely because code runs.

Company completion requires the machine-readable manifest and `docs/DEFINITION_OF_COMPANY_DONE.md` gates: organization, governance, runtime, Skills, standards, evidence, tools, UI, operations, packaging, relocation and offline validation.

## 9. Secrets and private assets

Never commit `.env`, tokens, model weights, proprietary customer data, local measurement datasets, private logs, instrument credentials or proprietary license material.

## 10. Publication boundary

This repo is explicitly the cloud construction site, so changes may be committed here when the Human requests construction. The upstream core repo remains read-only under all circumstances unless the Human separately changes that policy.