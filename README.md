# AERIS Portable Company Kernel — PRE-ALPHA

> **AERIS — Acoustic Engineering & Research Intelligence System**  
> 把同一套 AERIS 公司軟體、制度與可攜式執行核心部署到不同本機；不把「有架構」誤寫成「100 位成熟工程師已完成」。

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
               │ install / test / relocate
               ▼
Windows / Linux / Jetson / trusted-LAN local instance
```

Codex 永遠不得修改 `Space653000/0_JN1_AERIS`。若 implementation 與 Core 衝突，Core 勝出。

`core.lock.json` 鎖定已審查的 Core SHA；CI 執行 read-only Core drift gate。Core 若被 Human 更新，implementation CI 應先 FAIL，直到重新審查、實作並刻意更新 lock。

## 2. 現在真正成熟到哪裡？

目前產品階段：**PRE_ALPHA**。

Machine-readable truth：[`config/maturity.json`](config/maturity.json)  
完整反幻想審計：[`docs/AUDIT_REALITY_CHECK.md`](docs/AUDIT_REALITY_CHECK.md)

重要原則：

```text
NOT_IMPLEMENTED → IMPLEMENTED → TESTED → VERIFIED
```

- 100 seats 已有完整 registry 與 count test，但目前仍是 capability slots，不等於 100 位成熟工程師。
- Skills / Methods / Standards Registry / Dynamic Pod / Evidence Engine / G0–G5 / 專業工具 adapters / live local UI 仍需逐項完成。
- GitHub Actions 綠燈只代表 CI 實際執行的 kernel gates PASS，不代表整間公司 COMPLETE。

## 3. 零經驗安裝入口

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

### Linux / Jetson

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

Installer 會處理/檢查：

```text
Python >= 3.10
→ read-only Core sync / staged Core restore
→ local runtime prerequisite
→ local model
→ mode
→ machine detection
→ local Knowledge DB
→ unit/security tests
→ 100-role manifest
→ doctor
```

預設 local continuity model：`qwen3:4b-instruct`，透過 Ollama-compatible API。模型只是可替換算力，不代表 100 席專業能力；商用 release 前仍必須重新確認實際使用模型/tag/license。

詳細：[`docs/ONE_CLICK_INSTALL.md`](docs/ONE_CLICK_INSTALL.md)

## 4. 安裝完成 ≠ 本機已驗證

安裝後必跑 real-machine acceptance。

Windows：

```powershell
.\scripts\local-acceptance.ps1
```

Linux / Jetson：

```bash
bash scripts/local-acceptance.sh
```

它會實際驗：

- company manifest / 100-role registry；
- unit/security tests；
- local Knowledge build；
- Core cached clone push URL disabled + deny pre-push hook；
- local doctor；
- **真實 local inference**；
- offline mode doctor；
- **真實 offline-mode inference**。

若要宣稱 HARD OFFLINE，還要切斷/阻擋 external network 再跑：

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

或：

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

詳見 [`docs/security/LOCAL_NETWORK_ENFORCEMENT.md`](docs/security/LOCAL_NETWORK_ENFORCEMENT.md)。

## 5. 100-seat organization

AERIS 保留 100 個版本化 capability seats，依任務最終目標動態組成約 5–15 人 Temporary Pod，而不是啟動 100 個常駐 LLM process。

Registry：[`company/organization/roles.v1.json`](company/organization/roles.v1.json)

角色只有在具備並通過以下條件後，才可從「defined seat」升級成 verified capability：

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

目前是 **basic local SQLite text index**，不是完整世界級聲學 Knowledge System。

```bash
python -m aeris_runtime knowledge build
python -m aeris_runtime knowledge stats
python -m aeris_runtime knowledge search "beamforming"
```

DB：`.aeris/knowledge/aeris.sqlite3`。不做 cloud sync。

## 7. Privacy — Cloud 只允許公開研究入口

```text
PUBLIC INTERNET / CLOUD
        │ public query / public URL
        ▼
AERIS PUBLIC INGRESS
        │
        ▼
LOCAL STORAGE

LOCAL PRIVATE DATA ───X───► automatic cloud attachment
```

現在已實作的 application-level boundary：

- `aeris chat`：private engineering → **local AI only**；
- `aeris research`：public research only；不自動附加 local files / Memory / Evidence / customer data；
- public query 有 best-effort DLP screening；
- `aeris ingress URL`：阻擋 loopback/private/link-local SSRF 與 unsafe redirect；
- `offline`：禁止 AERIS cloud model routing 與 public URL ingress。

這不等於「整台 OS 所有 process 永遠不可能外流」。高機密部署必須再加 OS/firewall/process isolation。詳見 [`docs/security/LOCAL_NETWORK_ENFORCEMENT.md`](docs/security/LOCAL_NETWORK_ENFORCEMENT.md)。

## 8. Portable software ≠ private company state

`package-company.*` 現在故意只建立 **software-only package**，並排除：

- `.env`
- `.aeris/`
- `data/`
- `logs/`
- `portable_assets/`
- private backups

因此不會再把普通 ZIP 說成完整公司搬家。

私有狀態必須另外用現代加密：

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
```

AERIS 使用外部 `age` CLI；如果 `age` 不存在就拒絕假裝做安全加密。Restore/relocation SOP：[`docs/deployment/STATE_BACKUP_RESTORE.md`](docs/deployment/STATE_BACKUP_RESTORE.md)。

完整搬家 =

```text
Software Company Image
+ Encrypted Private State
+ Human-controlled Private Asset Pack
+ Restore / Tool / Local Acceptance
```

## 9. Professional tools

COMSOL、MATLAB、APx、KLIPPEL、SoundCheck、ACQUA、Ansys、Simcenter、專用 driver/license/hardware 不直接存入 public Git。文件存在不等於 adapter 已完成。

只有在合法安裝 + version capture + adapter + E2E + calibration/evidence（適用時）通過後才能標 `VERIFIED`。

詳見 [`docs/deployment/PROFESSIONAL_TOOLS.md`](docs/deployment/PROFESSIONAL_TOOLS.md)。

## 10. 核心真值

```text
Core GitHub
= AERIS 應該成為什麼

Portable implementation GitHub
= AERIS 目前實際做到了什麼、如何部署

Local runtime/evidence
= 這台機器實際發生了什麼
```

**Implemented is not Verified. CI green is not Company Complete. Dashboard is not Truth. Memory is not Evidence. Execution is not Completion.**
