# AERIS Astra 架構與 Implementation 審查記錄

日期：2026-09-07；review ID：AERIS-ASTRA-SOL-REVIEW-20260907。
**結論：設計可分期落地；目前 NO-GO for full build/opening。文件修訂完成不等於 runtime 缺陷已修復。**

## 範圍與固定點

- Blueprint：`82f4554623b2d87185dac39a3b93194af7dd5275`。
- Implementation：`32ca69baa778959d01c10a72bba1a8f0c0ac7eb5`；package 0.2.0，PRE_ALPHA。
- 使用者兩份 local proposal 已原文保存至 Blueprint `docs/research/inputs/2026-09-07/`；SHA-256 見 source_manifest。
- 全倉庫 tracked path 盤點、架構/治理/phase/配置對照、關鍵 runtime 信任／聲學路徑靜態審查、既有單元測試與三組 synthetic probes。未逐行證明所有功能無缺陷，未重新驗證原研究的全部市場數字、標準狀態或第三方相容性。
- 第 4 項 `C:\0_JN1_AERIS` 全面 Local 審查尚未開始；僅定位與讀取使用者指定的兩份 proposal。沒有讀取 .env 或私人 Evidence，也沒有執行 target 的 installer、Autopilot、服務、下載或真機驗收。
- 作者依使用者要求路由為 GPT-6 Astra High；官方文件支持該模型/high，但本工具紀錄不獨立證明 active UI model/effort。Sol 與最後 Astra 複核尚未執行，不能標獨立通過。

## 已觀察到的能力

`coverage_report()` 回傳 100 個 unique structurally valid contracts、domain_verified_count=0、roles_with_domain_asset_gaps=100。這是目前 generator 的明確旗標，不是對使用者 Local 工作的判決。

已註冊 deterministic Skills 3 個：measurement-import-validation、frequency-response-analysis、requirement-verification。Golden manifest 有 5 個 FR regression cases，包含 nominal、requirement pass/fail、duplicate rejection；不是 full Speaker/Mic domain dataset。

## 阻擋發現與 disposition

| ID / 嚴重度 | 證據與結果 | 後果 | 本次處理 / 未來關閉條件 |
|---|---|---|---|
| F01 / P0 | [aeris_runtime/taskstate.py:84](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/taskstate.py#L84); synthetic probe 所有 G0–G5=NOT_RUN，仍以非空 authority 與不存在 evidence ref 逐步進 RELEASED。 | 文字狀態可偽裝正式核准，並非有權對外發布。這是 module/CLI trust-boundary 反例，不宣稱未驗證的 remote network exploit。 | 文件改為必須解析 gate/evidence/approval artifact；B00 封鎖越權與重放，runtime 仍 OPEN。 |
| F02 / P0 | [aeris_runtime/verification.py:35](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/verification.py#L35), [aeris_runtime/claim_guard.py:58](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/claim_guard.py#L58), [aeris_runtime/controlplane.py:366](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/controlplane.py#L366);不存在 ref 可產生 G4 PASS，caller 同時提供 approved refs 時 Guard accepted=true。 | 字串白名單與不同 reviewer 名稱不證明證據存在或審查独立。 | 加 task/scope/hash/時效 resolver、可信 reviewer identity/context 與 Human approval；不存在/錯 task/篡改/過期/同作者變名全部拒絕，尚未實作。 |
| F03 / P1 | [aeris_runtime/controlplane.py:59](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/controlplane.py#L59), [aeris_runtime/taskstate.py:14](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/taskstate.py#L14), [aeris_runtime/workflow.py:111](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/workflow.py#L111); UI SQLite TASK-* 與 workflow JSON AERIS-* 分別建立任務。 | Mission、task list、workflow/evidence 狀態可能彼此脫鉤。 | 規定單一 identity/write authority 或明確雙向關聯 adapter；完成 create→execute→review→report→UI 同一任務契約及 crash reconciliation 才閉合。 |
| F04 / P1 | [aeris_runtime/skills_runtime.py:112](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/skills_runtime.py#L112), [aeris_runtime/skills_runtime.py:143](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/skills_runtime.py#L143); 100,100,1000 Hz 資料 import FAIL，20–20000 Hz requirement 卻 PASS。 | 使用者可能將樣本統計誤認完整需求頻段已驗證；直接 skill 路徑跳過統一驗證。 | B01 明定 coverage/grid/units/reference/uncertainty與相同入口校驗；負例輸出 BLOCKED/FAIL，現在仍 OPEN。 |
| F05 / P1 | Core master §9 vs 新提案 D01–D10：R100 Autonomous Experiment、A100 Reviewer；原 runtime IDs 由列表位置產生。 | 直接換號造成責任、證據與 reviewer routing 錯綁。 | 新版固定 100 個 R-ID 設計 registry；Axxx 不當 alias。跨表映射與 runtime immutable ID adoption 待獨立審查及未來實作。 |
| F06 / P1 | Core/Implementation AGENTS、P01 SOFTWARE_LOCAL_FIXABLE=0、P02 100_role_L2=100/100 無單批範圍；兩 URL 可觸發自動續建。 | review request 被誤解成施工；無界 backlog 導致重複重工。 | 全入口前置 hold；B00–B05 finite plan。JSON/文件不是 runtime guard，existing commands 仍不得執行，admission 實作 OPEN。 |
| F07 / P1 | [aeris_runtime/role_contracts.py:93](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/role_contracts.py#L93), roles planner、machine qualification config。 | 同一組 baseline asset 不等於每角色 domain capability；role count 不等於 inference concurrency，無法保證 J4012 16GB 或其他機器速度。 | role×capability×scope matrix、初始單重型 job、實測 admission/resource budgets；100-role professional readiness 未證實。 |
| F08 / P1 | Core 舊研究 R0–R3／Ask→Discover、Implementation R0–R4／L0–L4／platform maturity 與新提案生命周期。 | 相同「成熟／核准」可能指不同 gate。 | v0.6 定義多軸成熟度與 R0–R4；舊章節標示歴史背景，不能直接互換分數。 |
| F09 / P1 | Voice 原文 cache key 未包括所有 output/runtime/privacy 參數，job/cache 延後，PDF/EPUB phase互有出入，未區分 bit-identical。 | 錯誤重用、私密資料污染與假可重現、讀錯技術數值。 | Voice v1 增補 rights、source mapping、job recovery、完整 cache key、數字/單位/發音與品質 gates。僅設計採納，backend/license/performance NOT_TESTED。 |
| F10 / P1 | [aeris_runtime/reproduction.py:34](https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation/blob/32ca69baa778959d01c10a72bba1a8f0c0ac7eb5/aeris_runtime/reproduction.py#L34); replay 目前使用當下 run_skill，僅處理一個輸入，沒有重建歷史 executable environment。 | 相同結果可支持該 baseline 的結果重播，不能自動稱 historical environment reproduction。 | 規格要求 method/code/dependency/model hashes與兩種重現 scope；完整環境重建仍待建置。 |
| F11 / P1 | local qualification、hard-offline、reboot/persistence、license/calibration 均需指定 target evidence；此輪第4項被使用者保留。 | 遠端綠燈或靜態 spec 無法支持本機已完成宣稱。 | 保持 Local NOT_RUN，交 Sol 只讀；動態 acceptance 需後續授權，不得自行補跑。 |
| F12 / P2 | 使用既有 miniconda interpreter 跑 discover，site-packages/tests 遮蔽 repo tests；-S 隔離後通過。 | 未固定 Python 環境可能造成假失敗與重複修本機。 | 記錄環境差異；未修改 repo tests 或套件。後續使用乾淨、版本固定的 venv/CI驗證。 |

F01–F04 重現結果見 [audit-probe-results.json](audit-probe-results.json)。沒有真正產品發布、客戶資料或硬體動作。所有 synthetic state 都留於外部審查 workspace 的暫存目錄，並由 TemporaryDirectory 回收。

## 驗證紀錄與限制

- Core 原有 `python tools/validate-core-governance.py`：PASS。
- Implementation 原有 `python -m unittest discover -s tests -v`：172 tests / 1 import error（環境 tests namespace collision）。
- 同一原始碼 `python -S -m unittest discover -s tests -v`：174 tests / PASS；不載 site-packages，runtime 標準庫 baseline 可測。
- 所有產品 runtime、installer、test source 均未修補。此次另做的 synthetic probes 不計入既有 174 項，且揭露了現有綠燈未涵蓋的缺陷。
- 未執行本機 browser/service/model/driver/reboot/hard-offline acceptance；GitHub PR/main CI 結果由外部 publication record 記錄，不能事先自填 PASS。
- Kairos 當日 HTTP 只取得 loading shell，未證明 current UI visual，也未看到其 private backend；沿用倉庫 v0.5 使用者截圖校準作設計參考。其他 third-party 架構與市場評分當成 research input，不作驗證事實。

## 結論邊界

Blueprint v0.6.0-review.1 與 Implementation plan v0.3.0-review.1 的文義已對齊；五個 Core SHA pointers 在文件發布過程同一 Implementation commit 更新。這只是 document/source alignment，不能宣稱 Blueprint／Implementation runtime／Local 三者已一致。所有 P0/P1 runtime 缺陷保留為 OPEN；Sol、Astra reconciliation、Human scoped approval 是後續 gate。
