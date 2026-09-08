# AERIS Astra → Sol → Astra 審查閘門 v1

日期：2026-09-07。狀態：**HOLD_FOR_SOL_RED_TEAM / 不動工**。

目前使用者已授權第 1～3 項的架構輸入整併、Blueprint／Implementation 文件修訂與 GitHub 發布；尚未授權 AERIS 程式施工、安裝、部署或啟動。此審查契約優先於舊版兩個 URL Full-Build 觸發、所有缺口清零、P01/P02 自動續建及 optional reviewer 預設。

## 必須依序完成

1. GPT-6 Astra High：整併與架構／Implementation 審查，保留固定來源 SHA、重現結果與未解決項。文件發布不代表運作驗收通過。
2. 停下來，由使用者切換 **GPT-5.6 Sol High**。
3. Sol：讀取固定 Blueprint、Implementation 與 Local，獨立找出反例；只讀，不執行 installer、Autopilot、local acceptance wrapper、model download、service restart、reboot 或修補。若需要動態真機試驗，先列出必要操作供後續授權；本輪 Local review 可以以 NOT_TESTED/BLOCKED 結束，不能補造 PASS。
4. Astra：逐條回覆 Sol 的 P0/P1，修訂文件或引用原始證據駁回；涉及修訂的範圍重新交由 Sol 檢視，不能由原作者自行聲稱獨立通過。
5. Blueprint／Implementation／Local 一致性有可追溯記錄，且使用者明確核准有限的施工批次後，才准動工。

## 一致性記錄

記錄 `blueprint_sha`、`implementation_sha`、Local HEAD、dirty patch hash、必要 untracked source hashes、Core cache SHA、target path、configuration/model/asset digests、reviewer model/effort/context、finding dispositions、scope、time、expiry/invalidation rules。不公開 .env、密鑰、客戶檔、量測、私人 Evidence 或私人檔名清單。

Local 與遠端不同可以是合法的未發布工作；每項差異須分類為 accepted local overlay、待同步、待合併、未確認或衝突。不能只要求字串 SHA 相同，也不能 git reset/覆蓋 Local 來製造一致。任一受審 artifact 改動後，受影響的審查簽核失效。

## 權限與獨立性

本次 Core 文件發布是使用者明確授權的獨立治理作業，正常部署仍維持 Core read-only。Sol 不是常駐依賴；此次 Red-Team 是使用者指定的必要閘門。

同一 task 切換模型仍會繼承歷史，只有模型差異，沒有完整上下文隔離。Sol 應先從固定原始檔獨立形成發現，再對照 Astra 報告，並揭露 inherited-context 限制。若日後採新 task 或另一 harness，須保留相同來源與引用。

Core `aeris.review.json`／本倉庫 `config/review_gate.v1.json` 是治理記錄；目前沒有 runtime 強制器。README 或 JSON 的 HOLD 不等於舊 shell 程式會拒絕執行。舊命令目前不得啟動，執行式 admission gate 列為未施工的阻擋項。

## 兩個 URL 的剩餘語義

只有在 HOLD 已由完整審查及 Human 範圍授權解除，且訊息沒有 review／plan-only／不動工限制時，兩個 URL 才可触發授權批次。缺口清零只量化已凍結的批次清單；新發現進下一批 backlog。階段進入條件、輸入／輸出、驗收與停止條件未齊全時保持 BLOCKED，不因為軟體免費就自動納入。
