# CODEX_WORKER — Codex 施工契約

Codex 負責本專案的實作、修改、測試及修正。Claude Code 負責藍圖、Review 與獨立驗收；
Human Chief Engineer 作最後決定。Core Blueprint 是設計來源，Implementation 是施工來源。

## 每次開工

1. 在唯一正式施工根目錄 `C:\0_JN1_AERIS`，依序讀完
   [`BLUEPRINT.md`](BLUEPRINT.md)、[`ACCEPTANCE.md`](ACCEPTANCE.md)、[`STATUS.md`](STATUS.md)。
2. 重新核對固定 Blueprint tag／SHA、Implementation `main`、工作分支、PR、running
   runtime 與 Supervision snapshot。把差異與阻塞記入工作紀錄；過期的 STATUS 數字須以
   即時證據更正。
3. 從 `STATUS.md` 選一個明確未完成且符合當次使用者授權的項目，讀該項的原始規格、
   程式碼與測試。若當次要求停止施工，僅完成已指定的治理或盤點工作。
4. 確認該項的輸入、預期輸出、驗收條件及停止條件。涉及 Core 改版、正式核准、
   真機切換、外部授權或其他 Human Gate 時，保留證據並交由有權者決定。

## 施工與驗證

1. 修改前先執行相關既有測試並記錄結果；依 Blueprint 小步修改，為修正加入能重現
   問題的測試。
2. 每步執行受影響測試。完成該批工作後執行適當的完整回歸及雙平台 GitHub CI。
3. 逐項核對 `.ai/ACCEPTANCE.md` 的 Evidence：實際執行、Expected／Actual、
   PASS／FAIL、log／輸出與 Requirement ID。測試通過只證明測試範圍；正式驗收由
   Claude Code 獨立 Review，Human 專屬關卡由 Human 核准。
4. 更新 `.ai/STATUS.md` 的已完成、未完成、阻塞、版本、驗證指令與證據路徑；
   未達驗收的項目維持 `FAIL`、`UNKNOWN` 或 `NOT VERIFIED`。
5. 檢查 `git diff` 與暫存清單，僅提交本批可公開的來源及文件。使用簡潔英文
   `type: summary` commit 訊息，推送到對應工作分支與 GitHub PR；檢查該 commit 的
   CI 結果並將結果寫回 STATUS。後續狀態更新另以新 commit 推送。

## 權限邊界

- 以 Core `v0.7.0-blueprint.1` 為固定設計基線；Core 變更走獨立藍圖流程。
- 依當次使用者要求與現行 gate 工作；歷史自動續建文字不會自行授權新階段。
- 本地 `.env`、憑證、客戶資料、量測原件、私人 Evidence 與執行狀態留在本機。
- 對 PR、CI、runtime、Evidence 的完成狀態分別記錄，不以其中一項代替其他項。
