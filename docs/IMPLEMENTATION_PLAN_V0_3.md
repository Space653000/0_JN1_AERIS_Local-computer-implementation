# AERIS Implementation Plan v0.3.0-review.1

狀態：**HOLD_FOR_SOL_RED_TEAM / PLAN ONLY**；程式版本仍為 0.2.0 / PRE_ALPHA。此版修訂執行規格，不實作下列功能，不將既有 TESTED 升成 VERIFIED。

## 權威與順序

先讀 [review gate](ASTRA_SOL_REVIEW_GATE_V1.md) → [Astra findings](reviews/ASTRA_REVIEW_20260907.md) → pinned Core v0.6 → 本計畫 → phase catalog。P01/P02 保留為歷史全局建設目標；本計畫的有限批次與 review hold 優先於其「一直做到全清」語句。

## 施工前 admission

目前只允許文件發布及隔離軟體檢查；Sol Local review 未執行。Sol 完成只讀差異檢查、Astra reconciles、三方 baseline tuple 建立且 Human 核准有限施工 scope 後，才可開始該批。這不要求既有缺陷先修好才准寫任何 code；它要求修復計畫已被獨立檢查。首批只能修復阻擋信任基礎的缺陷，正式發布及開幕仍被 P0/P1 runtime defects 阻擋。

既有 shell/runtime 不消費 review_gate，新 JSON 是治理契約而非可執行阻擋。核准後首批補 entrypoint admission，覆蓋 installer/autopilot/start/resume/direct CLI/HTTP mutation；缺 artifact、過期、scope/SHA/target mismatch 或任一 HOLD 時拒絕。CI smoke 只用 sandbox fixture，不能產生 real-machine opening。

## 有界批次（目前全部 disabled）

| 批次 | 前置 | 有限交付 | 完成 oracle / 停止条件 |
|---|---|---|---|
| B00 Trust repair | Sol + Astra + Human scoped implementation approval | admission、task single-writer、G0–G5 integration、evidence resolver、authenticated Human/reviewer boundary | F01/F02/F03 負例拒絕；越權、錯 task、篡改、stale、重放／race 可重現；無真實 release。 |
| B01 FR vertical slice | B00 software checks pass | import→method→requirement→evidence→review→report→UI，統一頻段/單位/重複值檢查 | F04 失敗資料不可 PASS；至少 nominal/boundary/failure/invalid-input/reproduction cases，每案預先固定 oracle。 |
| B02 Mic/array slice | B01 evidence reviewed | 只選一個明確 capability，如 geometry/TDOA baseline，綁 canonical R-ID | 明示座標、units、sample rate、sync、array geometry、speed of sound、aliasing/反射限制；與獨立 oracle 比較、負例與不確定度通過。 |
| B03 Role expansion | 已評估方法與資料可用 | 每批最多 10 個角色/能力 scope，固定 IDs，逐席登錄 L0–L4 evidence | 角色有真 executable path，且不得把共用 helper 重複計成人類等效 domain coverage；無新 scope 偷渡。 |
| B04 Voice MVP | B00/B01 + local backend license/resource/language decision | Markdown/TXT、正規化／字典、單一持久 job、local TTS、WAV/MP3、Evidence | Core VP-01～08 適用項全過；無字幕則明示不支援；不對外發布。 |
| B05 Document/audio expansion | B04 reviewed | 每批擇 PDF/OCR 或 EPUB 或 subtitle/M4B 一項 | 新 parser/license/security/golden fixture 先行；無界整本轉換禁止。 |

Anchor 應依實際專案選 canonical roles，不按 A001/A011 等十進位編號直接對應。候選 FR Pod 可用 R001、R015、R079、R098、R099；實際職能/領域/衝突／資源需逐案通過。新 A046 SRP-PHAT 等先提出 many-to-many mapping，不改寫 R046 OTC Hearing Aid。

## 每批可執行契約

批次必填：batch_id/version、固定 capability IDs、input/model/method digests、實際 scope、owner、reviewer context、PR baseline、允許操作、dependencies、test oracle/tolerances、command allowlist、artifact paths、risk、人類核准、resource/deadline/budget、rollback、stop reason。未填欄位是 PLAN_INCOMPLETE，不可進自動化。

採同一軟體 scope 的 deterministic tests → Windows/Ubuntu PR CI → merge → merged main CI。尚未具备 target evidence 的項目留 NOT_TESTED；只在後續已授權的 target acceptance 階段進行 inference、斷網、reboot/persistence/load。需要新增權限、資料、授權或擴 scope 時保留 checkpoint 並停止，已凍結批次剩餘缺口為零即可結束，新發現進 backlog。

## 資源／模型／工具選型

不把 Astra/Sol 審查模型寫入 AERIS local provider。初始一個重型 inference slot，CPU分析/TTS與LLM依實測記憶體預算排隊。目標機的 OS、RAM/VRAM、driver、Python、Ollama、模型 weight digest、context、license與實測 latency/thermal/offline/persistence 由後續階段確認，本次不偵測或安裝。

Voice backend 需固定 upstream revision、code/model/voice各自授權、offline asset manifest、依賴鎖、zh-TW/en-US聽測、source/code hashes。未決 backend 是 B04 外部選型前置，不影響先審 B00/B01。專有工具未取得版本／授權／硬體／校正／E2E 時維持 BLOCKED_EXTERNAL；free method 只宣稱自己的 scope。

## 回滾與跨倉庫

本次文件透過 git revert 可回復，但 review hold 的解除需要 Human 明確授權，不能藉回復舊版繞過。未來 runtime migration 需先保存資料與 schema，證明 restore；不執行 destructive reset。Core 發布後五個 SHA pointers 在同一 Implementation commit 更新，candidate/document-aligned 不代表 runtime compliant。任何雙 repo 時間差由 drift gate fail closed；不得暫停或放寬 drift gate。

Local 是第三個尚未審查的 baseline，不將新版 remote 自動 pull 到 C:\0_JN1_AERIS。Sol 比較所有受審來源及 local overlays，Astra 判定保留／合併／待修後才提出有限同步方案。

## 1000 字內評估結果（第 3 項）

Implementation 已具備可用的軟體基礎：100 份契約、3 個確定性聲學 Skill、5 個 Golden 案例，隔離 Python 環境下 174 項單元測試通過。然而這些測試未證明完整信任鏈：暫存反例顯示 G0–G5 未跑仍可进入 RELEASED，不存在的 Evidence 字串可被接受，含重複頻率與不完整頻段的輸入也可得到 requirement PASS。UI task 與工程 task 分別存放，需要單一識別與狀態對帳。新版將原無界續建拆為 Trust 修復、FR、Mic/array、逐批擴角與 Voice，並保留本機／校正／離線／重啟驗收。上述缺陷尚未修復，不應宣稱專業公司已完成；先完成 Sol 獨立檢查與 Astra 三方複核，再核准首個修復批次。
