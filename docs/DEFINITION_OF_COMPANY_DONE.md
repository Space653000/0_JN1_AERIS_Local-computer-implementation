# Definition of AERIS Company Done

AERIS 不因「程式能跑」、CI 綠燈、100 個角色名稱存在或 AI 說完成，就宣稱整間公司完成。

Machine-readable maturity SSOT：`config/maturity.json`。  
Reality audit：`docs/AUDIT_REALITY_CHECK.md`。

## Allowed maturity states

```text
NOT_IMPLEMENTED
→ IMPLEMENTED
→ TESTED
→ VERIFIED
```

外部商用工具/硬體尚未具備時可用 `BLOCKED_EXTERNAL`。

`VERIFIED` 必須有與該 capability 相符的 evidence；不能用 README、UI badge 或 LLM judgment 升級。

## Company Gates

- **C0 Foundation** — repository/manifest/installer/CI + truthful maturity matrix
- **C1 Governance** — constitution/risk/authority/Core read-only boundary; Core server-side protection must be Human-configured
- **C2 Organization** — 100 role contracts + dynamic pod routing; not only 100 names
- **C3 Knowledge** — versioned Skills/Methods/Standards + reviewed local corpus + searchable DB
- **C4 Engineering** — Speaker/Mic × six disciplines executable/validated workflows
- **C5 Product** — product playbooks / lifecycle / requirement patterns
- **C6 Trust** — Evidence/Verification/Reproduction/Audit engines
- **C7 Tools** — CAE/lab/firmware adapters + version/calibration provenance + real-tool E2E
- **C8 Experience** — local Dashboard/Workspace/Services connected to live truth
- **C9 Operations** — health/expected-run/backup/recovery/rollback/observability
- **C10 Portable Offline** — clean-machine relocation, local model, real inference, reboot and hard-offline test
- **C11 Privacy** — application DLP + public-ingress safety + selected local OS/network isolation profile
- **C12 Zero-Experience Install** — supported clean machine completes guided one-click bootstrap and real-machine acceptance
- **C13 Business** — service catalog / delivery / quality / Human approval / legal & license checks
- **C14 Relocation** — software image + encrypted private state + Private Asset Pack + restore verification on a second machine

## Hard acceptance targets

```text
Core repo unauthorized Codex write                     0
Core server-side protection / credential boundary       VERIFIED BY HUMAN/GITHUB
Local private data automatic AERIS cloud attachment     0
Offline AERIS cloud-model calls                         0
Offline AERIS public-URL ingress                        0
False-Done                                               0
Unauthorized R3/R4 action                                0
Role registry count                                    100
Verified role capability coverage                      100% before "100 engineers ready"
Tier-A Evidence completeness                           100% applicable
Clean-machine relocation                               reproducible
Knowledge DB                                            local-only
Deployment report                                       generated
Real local inference                                    PASS for local/offline-ready machine
Hard-offline network acceptance                         PASS before air-gap claim
Encrypted private-state restore                         PASS before full relocation claim
Professional tool adapter E2E                           PASS per tool before HEALTHY
```

Unavailable proprietary software/hardware must report `NOT_CONFIGURED` / `BLOCKED_EXTERNAL` / `REMOTE_ONLY`, never fake `HEALTHY`.

## Forbidden completion shortcuts

The following do **not** prove Company Done:

```text
GitHub Actions green
100 role names
model answers one prompt
installer exits zero in CI smoke
professional-tool deployment README exists
static Dashboard looks healthy
AI reviewer says "looks good"
```

The release authority must inspect the actual maturity/evidence for every required gate.
