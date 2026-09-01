# AERIS — 本機只跑一次的最終驗收 SOP

目的：GitHub/CI 能證明的全部先在雲端證明；不要用本機 Codex 反覆試錯燒 Token。

## 給 Codex 的唯一正常入口

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
<LOCAL_TARGET_PATH>

請依 AERIS_AUTOPILOT 全自動部署、驗收、開幕並持續運行。
除非遇到真正 Human Gate，否則不要問我，也不要把可自動偵測的步驟丟回給我操作。
```

Codex 應自行：取得/更新 Implementation → 讀 Core → 執行 `AERIS_AUTOPILOT` → 安裝/盤點 → 真實 Local/Offline inference → Company Opening → 註冊 unattended persistence → 啟動 Dashboard → 留下 Evidence。

## 本機只需要一個驗收週期

Autopilot 成功後，只有 GitHub 無法替代的實機證據需要完成一次：

1. 確認 `.aeris/state/AUTOPILOT_RESULT.json` 為 `PASS_OPEN_VERIFIED_SCOPE`。
2. 確認 `.aeris/state/UNATTENDED_INSTALL.json` 已註冊 persistence；fallback 必須明示 limits。
3. 由 Codex 檢查 `http://127.0.0.1:8765/` 是 Dashboard，不是 `/health` JSON。
4. **唯一真正 Human Gate：**允許一次 Windows 重開機／登出登入，或 Linux/Jetson reboot/session restart，用來證明自啟與 recovery。
5. 回來後 Codex 自動確認 Dashboard 恢復、`UNATTENDED_OPERATIONS.json` 為 `HEALTHY`/`RECOVERED`，再執行 `CLAUDE_VERIFY_AERIS` 作獨立驗收。

若任何一步失敗，Codex 應讀 Evidence/Log 自行修復可自動修的項目；只有 admin/OS policy、License/EULA、Secret、實體接線/校正、Core policy、R3/R4 formal release 才詢問 Human。

## 不得誤宣稱

- CI PASS ≠ 使用者電腦已 VERIFIED。
- Dashboard alive ≠ 整間公司所有能力 HEALTHY。
- 100 callable seats ≠ 100 個 domain-verified 專家。
- Local Knowledge ≠ Evidence。
- 外部專業工具沒有 License/硬體/校正 Evidence 時只能 `BLOCKED_EXTERNAL`。

這份 SOP 的目的就是：**本機只做一次必要的真實世界驗收，不再把 GitHub 可抓的軟體 bug 留給本機 Codex 消耗 Token。**
