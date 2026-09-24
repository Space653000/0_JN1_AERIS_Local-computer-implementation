# AERIS BLUEPRINT — 本專案唯一藍圖依據索引

> 本文件不新增或改寫任何設計；它只**索引與引用**已存在的藍圖來源，方便每次接手時一次讀完。
> 依 GATE-01（見下方 constitution 摘要），唯一 Architecture / Design Source of Truth 是
> `Space653000/0_JN1_AERIS`（Core repo）。本文件與被索引的原始檔案都沒有被刪除或改寫。

最後盤點時間：2026-09-24（依即時查詢 GitHub API 與本機檔案系統，非記憶推測）。

## 0. 三個 GitHub Repository 的角色分工

| Repository | 角色 | 定位 |
| --- | --- | --- |
| [`Space653000/0_JN1_AERIS`](https://github.com/Space653000/0_JN1_AERIS) | **Core / Blueprint** | 唯一設計真相（GATE-01）。read-only，禁止 Implementation 自行發明架構。 |
| [`Space653000/0_JN1_AERIS_Local-computer-implementation`](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation) | **Implementation（本 repo）** | 只落實已核准 Blueprint（GATE-02）。本機 `C:\0_JN1_AERIS` 是唯一正式 Runtime/Product 環境（GATE-03）。 |
| [`Space653000/0_JN1_AERIS_Supervision`](https://github.com/Space653000/0_JN1_AERIS_Supervision) | **Supervision / 不可變快照鏈** | 發布 `S0001→S0002→...` 不可變快照（`LATEST.json` 為方便指標，不是權威本身）。與 `.aeris/autopilot/MASTER_TASK.md` 提到的本機路徑 `C:\0_JN1_AERIS_PARALLEL_STAGING`（本機目前不存在此資料夾）是**兩個不同概念**，不要混淆。 |

即時查證指令與結果（2026-09-24）：

```text
Core main HEAD:            64576bdbe680170fc1ea27306d1a2ab494cac733
Core latest release tag:   v0.7.0-blueprint.1 (與 main HEAD 相同 commit)
Implementation main HEAD:  44c0e507b305a6708cd80b6be43a82e314959c0d
本 session 工作分支:        codex/autopilot/20260911-stateful-loop
  ahead_by main: 165, behind_by main: 0
  對應 PR: #42（DRAFT, OPEN, MERGEABLE，非文件中常提到的 #33）
Supervision 最新快照:       S0005（2026-09-09，distinctly stale — 未反映本 session 任何工作）
```

**已發現的文件與現實落差**（詳見 `.ai/STATUS.md` §已知落差）：`README.md`、`AGENTS.md`、
`handoff/construction/GATE06-R1/*` 多處提到「Draft PR #33」，但 PR #33 實際上已經
**MERGED**、且是完全不同的 head 分支（`codex/handoff/H0001-P02-depth-368179b`）。本
session 實際對應的 Draft PR 是 **#42**。這是文件過期，不是新設計；BLUEPRINT 內容本身
未被質疑。

## 1. Core 的治理骨幹（GATE-01～08）

來源：`.aeris/core-reference/constitution.md`（本機快取，與 Core repo `constitution.md`
同步；版本 `0.7.0-governance.4`）。**完整原文請直接讀該檔案**，以下只是索引：

- **GATE-01** — Blueprint（Core repo）是唯一設計真相；Implementation 不得自行發明架構。
- **GATE-02** — Implementation 只能落實已核准 Blueprint；Core 的唯一程式例外是唯讀治理 validator。
- **GATE-03** — `C:\0_JN1_AERIS` 是唯一正式 Runtime/Product 環境；其他本機目錄不得冒充成果。
- **GATE-04** — Evidence Before DONE：沒有「實際執行＋可重現測試＋Expected/Actual＋PASS/FAIL＋Log＋Requirement ID」就不能標記 DONE。
- **GATE-05** — 禁止自我證明：重大功能需獨立審查者或獨立重新執行驗證，作者不得同 context 自行核准。
- **GATE-06** — Drift 立即停止：發現 Blueprint／Implementation／Local／Running service 四方不一致，STOP → REPORT → FIX → RE-VERIFY。
- **GATE-07** — 模型使用紀律：可替換操作路由，不是聲學 domain contract；不能為省 token 降低驗收標準。
- **GATE-08** — 一次只通過一個 Gate：Plan → Implement → Execute → Evidence → Verify → PASS → Next。

以及 15 條「保留既有聲學與安全要求」（LLM 推論不得寫成量測事實、工程數值附 unit/condition/
source、offline mode 禁止 configured cloud provider 等）——完整清單見原始檔案第 38–55 行。

## 2. Core 的定稿範圍與變更管制

來源：`.aeris/core-reference/BLUEPRINT_BASELINE.md`。

- 定稿版本：`v0.7.0-blueprint.1`；設計治理版本 `0.7.0-governance.4`。
- 定稿範圍：「一位人類主管，搭配 100 個聲學專業能力席位」——README 的「一人抵百人」是**產品願景**，不是已測得的效能或工程資格。
- 設計真相另見（皆在 Core repo，本機目前未鏡像，需要時向 Core repo 即時讀取）：
  - `constitution.md`
  - `docs/governance/AI_READ_ORDER.md`（完整讀取順序）
  - `docs/AERIS_BLUEPRINT_ZH_TW.md`（繁中總藍圖）
  - `docs/architecture/AERIS_UX_SKILL_EXAMPLES_V1.md`（UX 與技能範例規格）
  - `aeris.traceability.json`（需求契約）
- A–D 整體 **NOT VERIFIED**，E **NOT_STARTED**（Core 自己的定稿聲明，非本機推測）。

## 3. Core 的接手入口摘要

來源：`.aeris/core-reference/HANDOFF.md`。核心提醒：

1. 每次接手都要重新取得兩個 repo 的 `main` 完整 commit SHA，不能用網頁快取或對話記憶代替查詢。
2. 讀取順序：`AGENTS.md` → `constitution.md` → `AI_READ_ORDER.md` → 繁中總藍圖 → UX/技能範例規格 → 當批 Requirement。
3. 要把 Blueprint / Implementation / Local checkout / Running service 四方版本列在回報；發現 drift 先報告，只做有界治理修復。
4. 本機私有 Evidence 不必公開，但接手者未能取得時必須標記未核對。

## 4. Implementation（本 repo）自己的施工契約

- **`AGENTS.md`**（本 repo 根目錄）— 目前授權：GATE-06 RETRY R1；P0–P6 tracker 定義；
  Zero-prompt trigger；Mandatory default deployment profile。**完整內容見該檔案，未刪減**。
- **`.aeris/autopilot/MASTER_TASK.md`** — Continuous Autopilot 單批施工合約：一次只做
  一個 ready item、Evidence 格式、`AERIS_AUTOPILOT_TURN` machine-readable 區塊格式。
- **`docs/AERIS_P0_*.md` 到 `docs/AERIS_P6_*.md`** — P0–P6 各階段的詳細需求與完成證據
  （P0 穩定本機控制平面／P1 Kairos UX／P2 Progress Engine／P3 Golden Engineer／P4 技能教學／
  P5 Engineer Factory／P6 最終本機驗收）。
- **`docs/AERIS_PROFESSIONAL_COMPANY_BUILD_100_ENGINEER_CAPABILITY_FACTORY.md`** — 100
  席位能力工廠的詳細設計。
- **`handoff/construction/GATE06-R1/`**（`SUMMARY.md` / `CHECKLIST.md` / `COMPATIBILITY.json`）
  — 目前這一批候選修復的詳細範圍與否證測試清單，包含與 Supervision repo 的快照銜接規則。

## 5. 外部／候選參考（尚未整合，不能取代 Core）

`FRONTDESK_HANDOFF_BRIEF.md`（本 repo 根目錄，未追蹤檔案）提到一份**外部**文件：

> `C:\0_JN1_Offline-Local-Voice-Agent\AERIS_100_Acoustic_Engineers_Conversation_Record_v1.1_2026-09-15.md`
> （ChatGPT 深度研究，定義 Navigator → Orchestrator → 100 位聲學工程師 → Engineering Tools →
> Evidence → Delivery 六層架構）

**現況（2026-09-24 查證）：此檔案目前不存在於本 repo 任何位置**。這是一份來自另一個獨立專案
（語音代理人 Front Desk）的交接建議，尚未被使用者複製進來，也**不是** Core repo 的一部分。
依 GATE-01，即使日後複製進來，也只能作為候選/歷史參考，不能凌駕 Core 的唯一設計真相地位，
除非先修改 Core、升版、審查。列在此處是為了不遺漏，不代表已採納。

## 6. 如何重新驗證本文件裡的每一個數字

```bash
# Core / Implementation / 分支 SHA
gh api repos/Space653000/0_JN1_AERIS/commits/main --jq '.sha'
gh api repos/Space653000/0_JN1_AERIS_Local-computer-implementation/commits/main --jq '.sha'
gh api repos/Space653000/0_JN1_AERIS_Local-computer-implementation/compare/main...codex/autopilot/20260911-stateful-loop --jq '{ahead_by,behind_by,status}'

# PR 狀態
gh pr view 42 --repo Space653000/0_JN1_AERIS_Local-computer-implementation --json state,isDraft,mergeable

# Supervision 最新快照
gh api repos/Space653000/0_JN1_AERIS_Supervision/contents/LATEST.json --jq '.content' | base64 -d
```

不要把本文件的數字當成「永遠最新」；每次接手都應該重新跑一次上面的指令。
