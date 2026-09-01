# AERIS — 本機只跑一次的最終驗收 SOP

目的：GitHub/CI 能證明的先在雲端證明；本機 Codex 只做一次無法由 CI 取代的真機驗收。

## 給 Codex 的唯一正常入口

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
C:\0_JN1_AERIS\

請依 AERIS_AUTOPILOT 全自動部署、驗收、開幕並持續運行儀表板、前端、後端。
不要使用 Codex Tasks/排程；不要啟動 Claude Code 或其他額外模型驗收。
除非遇到真正 Human Gate，否則不要問我，也不要把可自動偵測的步驟丟回給我。
```

Codex 自行完成：同步 Implementation → 讀取只讀 Core → 盤點/安裝/設定 → Local/Offline inference → Company Opening → Dashboard/API → OS 原生自啟 → Watchdog → Evidence。

## 唯一真機週期

1. `AUTOPILOT_RESULT.json` 必須為 `PASS_OPEN_VERIFIED_SCOPE`。
2. `UNATTENDED_INSTALL.json` 必須顯示 persistence 已註冊；fallback 必須明示 limits。
3. Codex 驗證 `http://127.0.0.1:8765/` 為 Dashboard，前端與 API 可用。
4. 唯一正常 Human Gate：需要實證自啟時，請 Human 允許一次 reboot/logoff-login。
5. 回來後 Codex 自動確認 Dashboard/API、Supervisor、Heartbeat、Watchdog 已恢復，並寫入最終 Evidence。

不啟動 Claude Code。若 Human 日後另外要求獨立模型複核，再單獨執行 optional reviewer。

## 不得誤宣稱

CI PASS ≠ 真機 VERIFIED；Dashboard alive ≠ 全公司全能力 HEALTHY；100 callable seats ≠ 100 個 domain-verified 專家；外部工具缺 License/硬體/校正時仍是 `BLOCKED_EXTERNAL`。
