# AERIS Deployment Guides

AERIS deployment is intentionally split into **software install**, **real-machine acceptance**, **private-state relocation**, and **external professional-tool enablement**. No single step may pretend to prove the others.

## Start here

1. [`../ONE_CLICK_INSTALL.md`](../ONE_CLICK_INSTALL.md) — Windows / Linux / Jetson installer.
2. Run `scripts/local-acceptance.ps1` or `scripts/local-acceptance.sh` on the actual machine.
3. [`../security/LOCAL_NETWORK_ENFORCEMENT.md`](../security/LOCAL_NETWORK_ENFORCEMENT.md) — privacy assurance levels / hard offline.
4. [`STATE_BACKUP_RESTORE.md`](STATE_BACKUP_RESTORE.md) — encrypted Memory/Knowledge/Evidence/data relocation.

## Assets / models / tools

- [`LOCAL_AI_AND_MODELS.md`](LOCAL_AI_AND_MODELS.md) — local inference baseline, sizing and acceptance.
- [`PRIVATE_ASSETS.md`](PRIVATE_ASSETS.md) — model/installers/licenses/drivers/private data boundary.
- [`PROFESSIONAL_TOOLS.md`](PROFESSIONAL_TOOLS.md) — MATLAB / COMSOL / APx / KLIPPEL / SoundCheck / ACQUA / Ansys / Simcenter preflight rules.

## Truth rule

A guide means "how to deploy/verify"; it does **not** mean the corresponding product capability is already verified.

Current status is controlled by:

- `config/maturity.json`
- `docs/AUDIT_REALITY_CHECK.md`
- `docs/DEFINITION_OF_COMPANY_DONE.md`

## Portable relocation model

```text
Software Company Image
        +
Encrypted Private State
        +
Human-controlled Private Asset Pack
        +
Machine/tool-specific acceptance
        =
Actual verified AERIS instance
```

A software ZIP/tarball alone is not a full company relocation.
