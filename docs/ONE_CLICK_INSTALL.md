# AERIS One-Click Installation

目標：沒有開發經驗的人，拿到 repository/ZIP 後，只執行一個安裝入口即可建立 AERIS 公司基本執行環境。

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

Installer 會偵測/補 Python 3.11；優先使用 `portable_assets/installers/OllamaSetup.exe`，否則有 winget 時安裝 Ollama；再取得 local model、建立 SQLite Knowledge DB、驗證 100 roles、跑 tests/doctor、產生 deployment report。

## Linux / Jetson

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

Installer 自動辨識 apt/dnf/yum/pacman/zypper，缺 Python/venv/curl 時自動安裝。Ollama 優先採 `portable_assets/installers/ollama-install.sh`；若沒有離線 installer 且可連網，下載 `https://ollama.com/install.sh` 到 `.aeris/installers/`、記錄 SHA-256 後才執行。

## Air-gapped

真正完全斷網的新電腦必須事先在 `portable_assets/` 帶入需要的 inference installer/model/driver；商用 license 與 private data 仍由 Human-controlled Private Asset Pack 管理。

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
