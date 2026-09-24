# AERIS STATUS — 已完成 / 施工中 / 未完成 / 阻塞

> 每一條都附可重新驗證的指令或檔案路徑。找不到驗證方式的一律標 `NOT VERIFIED` /
> `UNKNOWN`，不寫「應該完成了」。盤點時間：2026-09-24。

## 0. 三方版本快照（依 `.ai/ACCEPTANCE.md` §7 的要求，每次都要重查）

```text
Core main HEAD:            64576bdbe680170fc1ea27306d1a2ab494cac733（= release tag v0.7.0-blueprint.1）
Implementation main HEAD:  44c0e507b305a6708cd80b6be43a82e314959c0d
本 session 工作分支:        codex/autopilot/20260911-stateful-loop（ahead 165 / behind 0，PR #42 DRAFT/MERGEABLE）
Supervision 最新快照:       S0005（2026-09-09）— 未反映本分支任何工作，DRIFT
```

## 1. 已完成（有 Evidence，可重新驗證）

### 1.1 Progress Truth / P0–P6（54 項機器可驗證清單）

- 重新驗證指令：`.venv\Scripts\python.exe -m aeris_runtime.progress_verify`
- 已知穩定通過 53/54；`P0.1` 偶爾因系統負載造成 flaky（`tests.test_controlplane` 的
  `test_five_plane_service_api_has_truth_fields` 等待背景遙測收斂逾時），重跑通常會過，
  不是邏輯錯誤。**這次盤點請以最新一次即時重跑結果為準，見本文件底部「本次即時重跑結果」**。
- Progress Center「FAIL_CLOSED 混淆」誠實性 bug 已修復（`aeris_runtime/progress.py`）：
  區分「證據不可信」與「只差人工核准這一個 acceptance gate」兩種情況，不再把兩者都顯示
  成一片 UNKNOWN。

### 1.2 本機系統穩定性修復

- **AERIS_START.ps1 卡住問題**：根因是腳本另外開一個獨立 `progress_verify` CLI 進程，跟
  正在跑的伺服器同時對同一批證據檔案讀寫，沒有跨進程鎖，實測卡死超過 1 小時。修法改成
  透過伺服器自己既有的 `/api/v1/progress/reverify` API 觸發（同一進程內的 single-flight
  機制），移除第二個進程而不是繞過症狀。已連續驗證 3 次乾淨執行（各 1.5–3 分鐘）。
- **`factory.materialize()` 遺失 `source_generation_core_sha` 欄位**：導致
  `blueprint_compatibility.validate()` 拒絕整批 Role Pack，伺服器完全無法啟動。已修復
  （`aeris_runtime/engineering/factory.py`），並補上 `tests/test_blueprint_compatibility.py`
  既有測試覆蓋這個 contract。
- 手機/平板版 mojibake（PowerShell 5.1 誤讀 UTF-8 為 Big5）、Cloudflare tunnel 網址自動
  重導向（`AERIS_START.ps1` 每次重啟自動 POST 新網址到 Worker KV）。

### 1.3 100 席位繁體中文說明（非樣板文字）

- `company/organization/roles_zh_tw.json`：全部 100 個角色的真實中文名稱與職能描述，
  來源是各角色自己的英文 mission，逐一翻譯，不是套版句子。之前只有 10/100 有真實翻譯，
  其餘 90 個顯示佔位文字「角色 NNN 專業工程席位」——這是使用者親自發現並要求修正的。
- `ui/web/skills-zh-tw.json`：全部 112 個領域技能都有真實繁中說明（原本缺 5 個）。

### 1.4 技能深度強化（第二／第三個真實不重疊技能）

即時查證指令：

```powershell
.venv\Scripts\python.exe -c "from aeris_runtime.engineering.professional_profiles import ROLE_DOMAIN_CONTRACTS as C; print(len([r for r,c in C.items() if len(c)>=2]),'/100 roles with 2+ skills;', len([r for r,c in C.items() if len(c)==1]),'with exactly 1;', 100-len(C),'with 0')"
```

現況：**37/100** 角色有 2 個以上（R079 有 3 個）；**56/100** 角色仍只有 1 個；**7/100**
角色（首席架構委員會 R001–R004, R006–R008）完全沒有領域技能，仍是 L1。

新增的 28 個技能全部遵循 `.ai/ACCEPTANCE.md` §4 的十步流程，公式來源與獨立驗證數值列在
每次 commit message（`git log codex/autopilot/20260911-stateful-loop`）與各
`methods/roles/*.json` 的 `uncertainty` 欄位。

### 1.5 端對端真實執行驗證（`scripts/exam_100_engineers.py`）

2026-09-24 執行結果（走真正 `run_role()` 生產流程，非單元測試捷徑）：

```json
{
  "roles_tested": 93,
  "skills_tested": 133,
  "cases_run": 579,
  "cases_evidenced": 579,
  "cases_failed": 0,
  "negative_cases_correctly_rejected": 153,
  "negative_cases_wrongly_accepted": 33
}
```

完整結果：`.aeris/evidence/exam_100_engineers_report.json`。

**579/579 個 positive/boundary/counter_hypothesis 案例 100% 產生真實 EVIDENCED 結果**，
且對其中一筆（R017 directivity-beamwidth）額外做了獨立 SHA-256 重新計算，10/10 檔案雜湊
吻合，證明證據封存包沒有被竄改。

## 2. 已知落差（真實發現，不是猜測）

### 2.1 「Draft PR #33」是過期引用

`README.md`、`AGENTS.md`、`handoff/construction/GATE06-R1/*.md` 多處提到「push only the
existing supervision branch/PR #33 as Draft」。即時查證（`gh pr view 33`）發現 **PR #33
已經 MERGED**，而且 head 分支是完全不同的 `codex/handoff/H0001-P02-depth-368179b`，跟本
session 的工作分支無關。本 session 實際對應的 Draft PR 是 **#42**
（`codex/autopilot/20260911-stateful-loop` → `main`，OPEN/DRAFT/MERGEABLE）。

**這是文件過期，不是設計被推翻**——`.ai/BLUEPRINT.md` 的 Core 治理骨幹內容本身沒有問題，
只是這幾份文件裡寫死的 PR 編號需要更新，尚未修正。

### 2.2 驗證漏洞：33 個負向案例被錯誤放行

`exam_100_engineers.py` 發現 33 個「本來應該觸發 ValueError 拒絕」的負向測試案例，實際上
被既有技能的 schema/驗證邏輯錯誤接受了。完整清單見
`.aeris/evidence/exam_100_engineers_report.json` 裡每個 `outcome: "WRONGLY_ACCEPTED_BAD_INPUT"`
的項目。**這是既有（本 session 之前就存在的）技能的真實驗證缺口，尚未修復**，屬於下一批
施工的候選項目。

### 2.3 外部參考文件尚未整合

`FRONTDESK_HANDOFF_BRIEF.md` 提到的
`AERIS_100_Acoustic_Engineers_Conversation_Record_v1.1_2026-09-15.md` 目前**不存在**於本
repo 任何位置（已用 `find` 全域搜尋確認）。見 `.ai/BLUEPRINT.md` §5。

### 2.4 三個未追蹤的根目錄檔案/資料夾，需要人類決定

以下檔案存在於本機工作目錄，`git status` 顯示未追蹤，尚未被任何一次 commit 收錄，內容
與用途已個別確認，但**是否要保留/整併/刪除需要人類決定**（依 GATE-03，本機刪除操作必須
謹慎，不主動刪除）：

- `FRONTDESK_HANDOFF_BRIEF.md` — 來自另一個獨立專案（語音代理人 Front Desk）的交接建議文件。
- `my_case.json` — 本 session 稍早手動測試 multi-step planner CLI 用的暫存測試資料
  （`speaker-power-distortion-baseline` 等技能的範例輸入），非正式產出。
- `html/` — 內含 `index.html` 與 `google467788a57c99a8a6.html`（Google Search Console
  網站驗證檔案），用途與部署目標不明，可能是另一個靜態網站殘留物。

### 2.5 `.aeris/autopilot/STATE.json` 是嚴重過期快照

該檔案的 `captured_at_utc` 是 `2026-09-11T14:03:18Z`，內容顯示 `overall: 0`、
`pass_count: 0`——這是本 session 大量工作**之前**的快照，跟即時 progress_verify 的真實結果
（98% 上下，見下方）差距巨大。**不要把這個檔案當成目前進度**；`MASTER_TASK.md` 說「outer
PowerShell runner 是唯一寫入者」，本 session 沒有透過那個 runner 執行，所以這個檔案沒有
被更新，是正常現象，不是新 bug，但容易誤導人，故在此明確記錄。

## 3. 未完成 / 阻塞（需要人類決定或大量工作）

1. **技能深度：剩餘 56 個單一技能角色**。其中約 50 個屬於已經很成熟的 Speaker/Microphone
   CoE 區塊（R009–R068），部分角色的既有技能已經是完整的第一性原理物理計算模組（例如
   `sealed_alignment.py`），必須先讀完既有程式碼才能判斷有沒有真正不重疊的空隙——已驗證
   可行的案例是 R017（-6dB 波束寬度）；已驗證行不通的案例是 R009/R011/R040。
2. **7 個首席委員會角色（R001–R004, R006–R008）完全沒有領域技能**，停留在 L1。這些角色
   本質上是跨領域判斷／架構仲裁角色，`docs/AERIS_P5_ENGINEER_FACTORY.md` 的 P5.2/P5.9 已
   明確記錄這是「刻意的、依角色本質而生的邊界」，不是還沒做完的缺口。
3. **33 個負向驗證漏洞**（見 §2.2）尚未修復。
4. **「真實零件知識庫」倡議**（使用者先前提出的第三項後續工作）完全未開始，卡在需要
   人類決定：人工整理／即時網路查詢／付費零件資料庫 API（Digikey/Mouser/Octopart）三選一。
5. **PR #33/#42 文件引用不一致**（見 §2.1）尚未修正。
6. **外部參考文件**（見 §2.3）尚未取得，需要使用者提供或明確放棄整合。
7. **未追蹤檔案處置**（見 §2.4）需要使用者決定。

## 4. 人類專屬關卡（依 `.ai/ACCEPTANCE.md` §6，AI 不能代勞）

- G5 正式簽核（`human_decide()` 需要具名人類核准者）。
- 真正的 Hard Offline 測試（斷網重開機）。
- Windows Task Scheduler 開機自啟排程複查。
- R3/R4 風險等級正式發布決策。

## 5. 本次即時重跑結果（用來驗證第 1.1 節）

2026-09-24 即時重跑 `python -m aeris_runtime.progress_verify` 的真實輸出：

```text
total: 54 non-PASS: 1
{
  "P0.1": {
    "result": "FAIL",
    "detail": "ran=22 failures=1 errors=0 modules=tests.test_site_zh_tw,tests.test_ui_core_ssot,tests.test_controlplane"
  }
}
```

**53/54 PASS，1 個 FAIL（P0.1）。** 這是誠實的即時結果，不是「應該過」的猜測。P0.1 涵蓋
`tests.test_site_zh_tw` / `tests.test_ui_core_ssot` / `tests.test_controlplane` 三個模組共
22 個測試，其中 1 個失敗、0 個 error。**尚未定位是哪一個具體測試案例失敗、也尚未判斷是
真實回歸還是先前懷疑的系統負載造成的 flaky（背景遙測收斂逾時）**——這是誠實盤點的一部分：
不確定就標示不確定，不假裝已經排查完。下一步（若使用者授權施工）應該是單獨重跑
`python -m pytest tests/test_site_zh_tw.py tests/test_ui_core_ssot.py tests/test_controlplane.py -v`
取得確切失敗案例名稱與 traceback，再判斷是回歸還是 flaky。**在查清楚之前，P0.1 標記為
`FAIL`，不得寫成「已完成」。**
