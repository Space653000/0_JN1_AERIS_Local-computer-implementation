# AERIS Portable Company Image

> **這個 repository 不是單純程式碼專案，而是 AERIS 的可搬遷公司映像。**
>
> Canonical design target / read-only SSOT: `https://github.com/Space653000/0_JN1_AERIS/tree/main`

## 兩個 GitHub 的權責

```text
0_JN1_AERIS
= READ-ONLY North Star / architecture / research / UI / governance SSOT
             │
             │ read / fetch / compare only
             ▼
0_JN1_AERIS_Local-computer-implementation
= PORTABLE COMPANY IMAGE / 全製作總工地 / 可執行公司映像
             │
             │ clone / ZIP / relocate
             ▼
任意 Windows / Linux / Edge AI 電腦
= 同一套 AERIS 公司在新地址重新啟動
```

**Codex 永遠不得修改 `Space653000/0_JN1_AERIS`。**

本 repo 則是 ChatGPT / Codex / Human 可以實際建設的總工地：公司章程、100 席位組織、Skills、Methods、Standards、Workflows、AI model routing、Tool adapters、Evidence、Memory、UI、部署、測試、備份與搬遷都應在這裡形成可版本化資產。

## 公司映像核心原則

1. **Self-contained software image**：clone/ZIP 後不依賴雲端才能啟動基本公司骨架。
2. **Local-first**：本地模型是永久最低可用能力；雲端模型是可插拔增強。
3. **Offline-capable**：`offline` mode 絕不呼叫 configured cloud provider。
4. **Model-neutral**：Claude、Codex、OpenAI-compatible cloud、Ollama/local model 都只是 replaceable runtime。
5. **Machine-portable**：公司身份、制度、角色、Skills、Methods、Evidence contracts 不綁特定電腦。
6. **Evidence-first**：Execution ≠ Completion；正式結果必須經 Evidence / Verification / Approval。
7. **Relocatable**：新電腦具備 prerequisite 後，解壓/clone + installer 即可恢復公司軟體與制度。

## Runtime modes

| Mode | 行為 |
|---|---|
| `offline` | 僅本地 AI；禁止 configured cloud provider。 |
| `local` | 固定本地 AI。 |
| `cloud` | 優先雲端；依政策可 fallback local。 |
| `auto` | local-first；本地不可用時才考慮雲端。 |

目前基線：Local = Ollama-compatible；Cloud = OpenAI-compatible；預設 local model = `qwen2.5:3b`。

## 一鍵搬遷

### Windows

```powershell
git clone https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation.git
cd 0_JN1_AERIS_Local-computer-implementation
powershell -ExecutionPolicy Bypass -File .\scripts\relocate-company.ps1
```

### Linux / macOS

```bash
git clone https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation.git
cd 0_JN1_AERIS_Local-computer-implementation
bash ./scripts/relocate-company.sh
```

## 打包整棟公司

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package-company.ps1
```

或：

```bash
bash ./scripts/package-company.sh
```

GitHub repo 本身不應承載數 GB 模型權重、credentials、customer data 或專有 CAE/量測軟體授權。若要製作真正 air-gapped bundle，可在打包前於本機建立 `portable_assets/`，放入授權允許攜帶的模型/installer/driver；打包腳本會把存在的資產一起封裝。

## 啟動與檢查

```bash
python -m aeris_runtime company status
python -m aeris_runtime doctor
python -m aeris_runtime mode show
python -m aeris_runtime mode set offline
python -m aeris_runtime chat "請回報 AERIS 狀態"
```

## 公司資產地圖

```text
company/             公司章程、組織、營運與商業模型
skills/              可版本化聲學工程 Skills
methods/             可驗證工程方法
standards/           標準版本與映射
workflows/           Requirement → Evidence → Verification 工作流
adapters/            CAE / lab / OS / data / firmware adapter contract
firmware/            韌體整合與版本邊界
ui/                  Dashboard / Workspace / Services 可攜 UI
memory/              可摘要、可演進的公司記憶
evidence/            工程事實與 Evidence Bundle 契約
portable/            公司映像與離線資產規格
scripts/             安裝、啟動、同步、打包、搬遷
aeris_runtime/       Local/cloud/offline AI runtime
tests/               Offline-safe automated verification
```

## 真值分層

```text
Core GitHub = AERIS 應該成為什麼
Portable Company GitHub = AERIS 公司如何完整存在並被搬遷
Local runtime/evidence = 這台機器實際發生了什麼
```

三層不可混為一談。