# AGENTS.md — AERIS Portable Company Image Contract

Repository: `Space653000/0_JN1_AERIS_Local-computer-implementation`
Canonical read-only target: `Space653000/0_JN1_AERIS@main`

## 1. Authority

`0_JN1_AERIS` = highest-priority design target. Codex may read/fetch/compare it but MUST NOT perform any GitHub write against it.

This repository is the executable Portable Company Image and may be changed when the Human requests implementation work. It may add deployment/runtime/machine adaptation, but MUST NOT override Core product/engineering direction.

## 2. Portable-company invariant

A checkout/ZIP must carry every redistributable asset required to reconstruct the same AERIS company identity, governance, roles, Skills/Methods, workflows, runtime, UI and verification system on another supported machine.

External assets are allowed only where legally/technically required: model weights, proprietary installers/licenses, customer data, drivers and credentials. Every external dependency needs a manifest/preflight/deployment guide.

## 3. Zero-experience installation target

Every change must preserve the one-click path:

- Windows: `INSTALL_AERIS_LOCAL.ps1` → `scripts/one-click-install.ps1`
- Linux/Jetson: `INSTALL_AERIS_LOCAL.sh` → `scripts/one-click-install.sh`

Installers must fail clearly, never silently claim success, and produce a deployment report.

## 4. 100-role company

`company/organization/roles.v1.json` is the executable role registry. It mirrors the Core role architecture and must remain traceable to the read-only Core. Runtime should dynamically assemble only relevant specialists, not start 100 persistent LLM processes.

## 5. Hard privacy / one-way cloud boundary

Default classification of local content = `LOCAL_ONLY`.

Forbidden to public cloud automatically or implicitly: local files; Knowledge DB/Memory; Evidence bundles; customer/project data; measurement/CAE/factory data; private history; instrument credentials; private telemetry payloads.

Private engineering `chat` is local-only regardless of selected mode.

Cloud is allowed only through `public_research` / ingress with **no local context attached**. Cloud/public information may be downloaded and persisted locally.

If a cloud task requires local private context, do not weaken privacy: use Local AI or report the limitation.

## 6. Offline invariant

When internet/cloud is unavailable, company control, role/knowledge lookup, local workflows, evidence handling, diagnostics and supported AI workflows must remain usable with local assets.

## 7. Model neutrality

Models are replaceable compute. Provider-specific behavior stays inside adapters. AERIS identity, role contracts, rules, Skills, Memory and Evidence must not depend on a model brand.

## 8. Start-of-task procedure

1. Confirm this is the implementation repo.
2. Read `company/company.manifest.json`, `aeris.local.policy.yaml`, `config/data_governance.json`, `README.md`.
3. Read applicable Core files read-only and record Core SHA.
4. Run `python -m aeris_runtime company status`.
5. Run `python -m aeris_runtime machine detect`.
6. Run `python -m aeris_runtime knowledge stats`.
7. Run tests and doctor.
8. State runtime mode, privacy impact and affected subsystem.

## 9. Completion evidence

Every delivery reports: Core SHA; Core write performed=NO; implementation SHA; changed subsystem; tests; doctor; privacy/egress result; offline result; knowledge DB impact; machine/deployment impact; remaining gaps.

## 10. No false-done

Working code is not equal to company completion. `docs/DEFINITION_OF_COMPANY_DONE.md` gates remain authoritative for implementation completion.
