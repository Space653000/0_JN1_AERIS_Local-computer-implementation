# AERIS One-Click Installation

目標：沒有開發經驗的人，拿到 repository/ZIP 後，只執行一個安裝入口即可建立 AERIS 公司基本執行環境。

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\one-click-install.ps1
```

安裝器會：偵測 Windows/CPU/RAM/GPU/architecture；建立 Python virtual environment；建立 `.env`、`.aeris/`、data、logs；Windows 有 winget 時自動補 Python/Ollama；有網路時嘗試取得 `qwen2.5:3b`；建立本機 SQLite Knowledge DB；驗證 100-role company manifest；執行 tests/doctor；產生 `.aeris/state/DEPLOYMENT_REPORT.json`。

## Linux / Jetson

```bash
bash ./scripts/one-click-install.sh
```

Linux 不會未經驗證地 `curl | sh` 執行遠端安裝器。若 Ollama 尚未存在，依 `LOCAL_AI_AND_MODELS.md` 或 `portable_assets/` 離線資產安裝。

## 使用者只要記住

- private engineering chat = 本地 AI
- research = 公開雲端研究入口，不帶本機資料
- knowledge = 本機 SQLite 專業知識/記憶資料庫

## 驗收

```bash
python -m aeris_runtime company status
python -m aeris_runtime machine detect --write
python -m aeris_runtime knowledge build
python -m aeris_runtime knowledge stats
python -m aeris_runtime doctor
```
