# GPT-5.6 Sol High 獨立 Red-Team：第 4 項交接

狀態：NOT_RUN。只有使用者切换为 GPT-5.6 Sol High 後繼續；此文件不是新的施工授權。

## 讀取與固定輸入

先確認模型/effort（可用 host metadata 或使用者選定設定，不能靠自述）。固定兩 repo main SHA，讀 Core review gate/current architecture/兩份原始提案與 Implementation current plan/source。取得本次發布的 exact commit tuple；main 若已改動先標 drift，不自行改 lock 或拉入 Local。

獨立性：先從原始來源形成自己的發現，再對照 Astra findings。當前 task 有繼承歷史；在報告揭露這個界限。不同模型不自動等於獨立證據。

## Local 僅讀清單

1. `C:\0_JN1_AERIS` 實際 root、repository role/remotes、HEAD/branch、tracked diff。檢查 reparse points/junction 邊界，exclude .git/.venv/model blobs 等再按需讀；不輸出 .env、keys、客戶內容。
2. 比較 Core cache SHA/guards、五個 lock pointers、active code/entrypoints、config、roles/skills/methods/golden、phase specs 及 local overlays。專業程式與生成 state 分開評估。
3. 現有 evidence 可讀取並驗證時間、hash、scope、來源 commit、target/environment、核准與已失效條件；現有 PASS 不等於此輪重跑成功。未知／缺檔要明寫 UNKNOWN/NOT_TESTED。
4. 針對 F01/F02 独立檢查 gate/auth/evidence 是否可偽造；F03 同一任務投影；F04 invalid/incomplete FR；role identity/maturity、resource、ingress/privacy、job recovery、license/standard freshness、Voice契約。
5. 不跑 Autopilot、INSTALL、START、local-acceptance、CLAUDE_VERIFY、model download、service restart、排程寫入、reboot、reset 或任何修補。需要動態實驗就列操作、目的與預期 evidence，留後續授權。

## 輸出

報告每條 ID、P0/P1/P2、source SHA + file/line、反例、影響、最小修正、關閉 oracle、是否阻擋 design approval／construction scope／opening。不要把所有修復完成才可開工寫成循環：可以核准有限修復批次，但不得核准未修妥的正式營運。

提出 Blueprint／Implementation／Local comparison matrix，每個差異分類為合法 local overlay、待同步、待合併、衝突或未知。保存 private diff/hashes 在 local outputs；沒有額外授權不向 GitHub 上傳任何 Local evidence、客戶資料或私人路徑清單。

最後：重點摘要 + 1000字內第4項評估 + 給 Astra 的逐條待處理清單。Local verdict 可以是 BLOCKED，不得為通過而修補。然後停下，讓使用者切回 Astra 複核。

## 最後 Astra 必須做

逐條 accept/modify/reject-with-evidence，核對所有固定 SHA/dirty overlays/必要資料與模型 digest；修訂會影響的範圍交 Sol 再查。只有三方差異皆有處置、沒有未解的施工計畫阻擋、Human 核准 finite repair scope，才可以開始該批。營運放行仍要求所有適用 runtime defects 與 real-machine gates 關閉。
