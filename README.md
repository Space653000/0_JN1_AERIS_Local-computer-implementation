# AERIS Portable Company Kernel — PRE-ALPHA

> **AERIS — Acoustic Engineering & Research Intelligence System**  
> 把同一套 AERIS 公司軟體、制度與可攜式執行核心部署到明確支援的本機；不把「有架構」誤寫成「100 位成熟工程師已完成」。

Canonical design target / read-only SSOT:  
`https://github.com/Space653000/0_JN1_AERIS/tree/main`

## 1. 兩個 GitHub 的權責

```text
0_JN1_AERIS
= WHAT AERIS MUST BE
= READ-ONLY North Star / Architecture / Research / UI / Governance
               │
               │ read / fetch / compare only
               ▼
0_JN1_AERIS_Local-computer-implementation
= HOW AERIS IS IMPLEMENTED AND DEPLOYED
= Portable Company Kernel / cloud construction site
               │
               │ branch → test → PR → main
               ▼
Supported local machine
               │
               │ real-machine acceptance
               ▼
VERIFIED AERIS instance for a specified scope
```

Codex/implementation 永遠不得修改 canonical Core。若 implementation 與 Core 衝突，Core 勝出。

`core.lock.json` 鎖定已審查 Core SHA；CI 執行 read-only drift gate。Core 若由 Human 更新，implementation 應先 FAIL，直到新 Core 被重新審查、實作並刻意更新 lock。

GitHub `main` 不是一般 AI 施工區；正常施工使用 feature/repair branch + CI + Pull Request。

## 2. Anti-fantasy truth

目前產品階段：**PRE_ALPHA**。

Machine-readable truth：[`config/maturity.json`](config/maturity.json)  
Reality check：[`docs/AUDIT_REALITY_CHECK.md`](docs/AUDIT_REALITY_CHECK.md)  
Human–AI cooperation：[`docs/AI_HUMAN_RELIABILITY_CONTRACT.md`](docs/AI_HUMAN_RELIABILITY_CONTRACT.md)  
本機驗收：[`docs/LOCAL_VERIFICATION_SOP.md`](docs/LOCAL_VERIFICATION_SOP.md)

唯一成熟度路徑：

```text
NOT_IMPLEMENTED
→ IMPLEMENTED
→ TESTED
→ VERIFIED
```

- 100 seats 有 versioned registry/count test，但仍是 capability slots，不等於 100 位成熟工程師。
- Skills / Methods / live Standards Registry / Dynamic Pod / Workflow Engine / Evidence Engine / G0–G5 / Golden acoustic datasets / professional tool adapters / live local UI 仍需逐項實作驗收。
- CI green 只代表 CI 真正執行的 kernel scope PASS；不代表公司完成。
- Supported Machine Profile 只代表有明確部署 baseline；不代表該台真機 VERIFIED。

## 3. 零經驗安裝入口

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

Linux / Jetson：

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

安裝器採 fail-closed：

- Python 必須 >= 3.10；
- offline 缺必要 staged prerequisite 時 BLOCK，不偷偷上網；
- requested LocalModel 與 runtime 設定必須一致；
- staged Python/Ollama/model 需要 checksum/manifest；
- canonical Core 必須能同步或由可驗證 snapshot 提供；
- unit/security tests / Company Manifest / doctor 都會執行；
- installer 結束仍只叫 `INSTALLED`，下一步一定是 real-machine acceptance。

詳細：[`docs/ONE_CLICK_INSTALL.md`](docs/ONE_CLICK_INSTALL.md)

## 4. 安裝完成 ≠ 本機 VERIFIED

Windows：

```powershell
.\scripts\local-acceptance.ps1
```

Linux / Jetson：

```bash
bash scripts/local-acceptance.sh
```

Acceptance 驗：

```text
Company Manifest
+ repository tests
+ self-cleaning Knowledge build
+ Supported Machine Profile
+ canonical Core integrity
+ local doctor
+ real local inference
+ offline doctor
+ real offline-mode inference
```

證據：

```text
.aeris/state/LOCAL_ACCEPTANCE.json
```

Hard offline 額外：

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

多路 outbound probe 任何成功都 FAIL；全部 blocked 也只記 `OUTBOUND_PROBES_BLOCKED_NOT_GLOBAL_PROOF`，不假裝有限測試是宇宙級零外流證明。

## 5. 100-seat organization

AERIS 保留 100 個版本化 capability seats，最終依任務動態組成約 5–15 人 Temporary Pod，而不是啟動 100 個常駐 LLM process。

Registry：[`company/organization/roles.v1.json`](company/organization/roles.v1.json)

每席只有具備以下證據後才可升級成 verified capability：

```text
Role Contract
+ Skills
+ Methods
+ Tool Permissions
+ Required Evidence
+ Golden / Negative / Regression tests
+ Acceptance Rubric
+ Independent Review
```

## 6. Local Knowledge / Memory

現在是 **basic local SQLite text index**，不是完整世界級聲學 Knowledge System。

```bash
python -m aeris_runtime knowledge build
python -m aeris_runtime knowledge stats
python -m aeris_runtime knowledge search "beamforming"
```

目前 hardening baseline：

- local only；
- Core cache + versioned implementation docs/text；
- rebuild 會移除被刪除/改名的 stale source；
- SQLite FTS5 可用時使用 FTS5，否則 LIKE fallback；
- public ingress 不自動進 Knowledge。

真正專業 acoustic corpus / semantic retrieval / provenance graph / WAV-HDF5-CAE knowledge 仍未完成。

## 7. Privacy — Private local, Public explicit

```text
PRIVATE ENGINEERING
local files / Memory / Evidence / customer data
        ↓
LOCAL AI / LOCAL TOOLS ONLY

PUBLIC RESEARCH
explicit public query
        ↓
best-effort DLP
        ↓
configured Cloud optional
        ↓
response saved locally
```

Public URL：

```text
DNS public-only check
→ validated IP-pinned TCP/TLS
→ redirect revalidation
→ QUARANTINE
→ SHA-256
→ malware scan if available
→ prompt-injection/content-risk markers
→ Human promotion
```

下載內容不會自動被 Knowledge 信任。

這是 AERIS application boundary，不等於「整台 OS 所有 process 永遠不可能外流」。高機密部署必須使用 [`docs/security/LOCAL_NETWORK_ENFORCEMENT.md`](docs/security/LOCAL_NETWORK_ENFORCEMENT.md) 的 P2/P3/P4 架構。

## 8. Air-gap Core / models

Core cache 可是：

1. guarded Git cache：push URL disabled + deny pre-push；或
2. checksum-manifested snapshot：沒有 `.git`、每個檔案 SHA-256 + canonical Core SHA。

```bash
python -m aeris_runtime core snapshot --output portable_assets/core-reference
python -m aeris_runtime core verify
```

Staged GGUF model 使用 `portable_assets/models/model.manifest.json` + file SHA-256；offline 缺合法/可用 model 時直接 BLOCK。

## 9. Portable software ≠ private company state

Software Image 故意排除：

- `.env`
- `.aeris/`
- `data/`
- `logs/`
- `portable_assets/`
- private backups

每個 Software Image 包含：

```text
release-metadata/
├─ SBOM.spdx.json
├─ PROVENANCE.json
└─ SHA256SUMS
```

這是 inventory/integrity/provenance，不等於 signed release/attestation。

私有狀態另用 `age`：

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
python scripts/private-state.py import private-backups/AERIS-private-state.age
```

Archive restore 拒絕 traversal、symlink、hardlink、device、FIFO 等危險 member。

完整搬家 =

```text
Software Company Image
+ Encrypted Private State
+ Human-controlled Legal Private Asset Pack
+ Destination Restore
+ Core / Tool / Calibration / Local Acceptance
```

## 10. Professional tools

COMSOL、MATLAB、APx、KLIPPEL、SoundCheck、ACQUA、Ansys、Simcenter 與專用 driver/license/hardware 不直接存 public Git。

只有：

```text
legal install
+ exact version capture
+ implemented adapter
+ E2E
+ calibration/evidence where applicable
+ acceptance
```

才能標 `VERIFIED`。

## 11. 核心真值

```text
Core GitHub
= AERIS 應該成為什麼

Implementation GitHub
= AERIS 目前真正做到了什麼、如何部署

Local runtime/evidence
= 這台機器實際發生了什麼
```

**Unknown > invented. Blocked > unsafe. Implemented is not Tested. Tested is not Verified. CI green is not Company Complete. Dashboard is not Truth. Memory is not Evidence. Execution is not Completion.**
