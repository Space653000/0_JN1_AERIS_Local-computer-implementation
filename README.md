# AERIS Portable Company Image

> **把整間 AERIS 聲學工程公司打包到任意本機，而不是只搬程式碼。**
>
> Canonical design target / read-only SSOT: `https://github.com/Space653000/0_JN1_AERIS/tree/main`

## 兩個 GitHub 的權責

```text
0_JN1_AERIS
= WHAT AERIS MUST BE
= READ-ONLY North Star / Architecture / Research / UI / Governance
               │
               │ read / fetch / compare only
               ▼
0_JN1_AERIS_Local-computer-implementation
= HOW AERIS ACTUALLY EXISTS AND RUNS
= Portable Company Image / Cloud construction site / executable implementation
               │
               │ clone / ZIP / relocate
               ▼
Windows / Linux / Jetson / trusted LAN deployment
```

**Codex 永遠不得修改 `Space653000/0_JN1_AERIS`。** 若 implementation 與 Core 衝突，Core 勝出，implementation 必須修正。

## 零經驗一鍵啟動

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

Linux / Jetson：

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

這兩個入口會轉入正式 one-click installer，目標自動完成：Machine detection → Python env → Local AI prerequisite → 100-role validation → local Knowledge DB → tests → doctor → deployment report。

詳見 `docs/ONE_CLICK_INSTALL.md`。

## 100 人聲學工程公司

AERIS 保留 100 個版本化 capability roles，依任務動態組成約 5–15 人 Pod，不是啟動 100 個常駐 LLM process。可執行角色表：`company/organization/roles.v1.json`。角色來源仍以唯讀 Core `0_JN1_AERIS` 為準。

## 本地專業知識 / 記憶資料庫

AERIS 使用 Python standard-library SQLite 建立本機 Knowledge DB：

```bash
python -m aeris_runtime knowledge build
python -m aeris_runtime knowledge stats
python -m aeris_runtime knowledge search "beamforming"
```

DB：`.aeris/knowledge/aeris.sqlite3`。索引公司制度、Skills、Methods、Standards、Workflows、Memory，以及唯讀快取的 Core。**不做 cloud sync。**

## 核心隱私：Cloud 只進、本地不出

```text
PUBLIC CLOUD / INTERNET
        │ public research / download
        ▼
LOCAL AERIS
        ├─ Local AI
        ├─ Knowledge DB
        ├─ Memory
        ├─ Evidence
        └─ Customer / Measurement Data

LOCAL PRIVATE DATA ───X───► PUBLIC CLOUD
```

所有本機資料預設 `LOCAL_ONLY`。

- `aeris chat` = private engineering channel，**永遠 local AI**。
- `aeris research` = public research channel，可用 cloud，但**不掛載 local files / Memory / Evidence / customer data**。
- `aeris ingress URL` = 把公開網路內容拉回本機並保存 hash/manifest。

```bash
python -m aeris_runtime chat "分析本機工程資料"
python -m aeris_runtime research "查公開的聲學技術資訊"
python -m aeris_runtime ingress "https://example.com/public-resource"
```

完整規格：`docs/PRIVACY_ONE_WAY_CLOUD.md`。

## Runtime modes

| Mode | 私人工程工作 | 公開研究 |
|---|---|---|
| `offline` | Local AI | Local AI only |
| `local` | Local AI | Local AI |
| `cloud` | **Local AI** | Cloud allowed |
| `auto` | **Local AI** | Local-first，必要時 cloud |

切到 cloud 不代表把私人本機資料送上雲端。

## Machine Profiles

Company Image 相同，硬體能力由 Machine Profile 決定：Windows CPU、Windows NVIDIA、Linux x86 NVIDIA、Jetson Orin/J4012、Human-approved trusted LAN AI server。

```bash
python -m aeris_runtime machine detect --write
```

輸出 `.aeris/state/DEPLOYMENT_REPORT.json`。詳見 `docs/deployment/README.md`。

## Professional tools / private assets

COMSOL、MATLAB、APx、KLIPPEL、SoundCheck、ACQUA、Ansys、Simcenter、模型權重、license、客戶資料與儀器 credentials 不直接進 public GitHub。AERIS 提供部署/preflight 契約；合法資產由 `portable_assets/` 在本機或離線包加入。

- `docs/deployment/PROFESSIONAL_TOOLS.md`
- `docs/deployment/LOCAL_AI_AND_MODELS.md`
- `docs/deployment/PRIVATE_ASSETS.md`

## 公司資產地圖

```text
company/             章程、100 roles、營運、商業模型
skills/              聲學工程 Skills
methods/             可驗證 Methods
standards/           Standards registry / lifecycle
workflows/           Requirement → Evidence → Verification
memory/              本地可演進記憶契約
knowledge/           本地知識資料庫規格
evidence/            immutable engineering evidence contract
adapters/            CAE / lab / OS / firmware adapters
firmware/            firmware integration boundaries
ui/                  Dashboard / Workspace / Services
config/              runtime / privacy / machine profiles
portable/            air-gapped company image rules
scripts/             install / run / sync / package / relocate
aeris_runtime/       runtime / privacy / knowledge / ingress / machine detection
tests/               offline-safe verification
```

## 真值分層

```text
Core GitHub = AERIS 應該成為什麼
Portable Company GitHub = AERIS 如何完整存在、運行與被搬遷
Local runtime/evidence = 這台機器實際發生了什麼
```

三層不可混為一談，也不可用 UI 綠燈取代 Evidence。
