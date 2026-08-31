# AERIS One-Click Installation — PRE-ALPHA

目標：沒有開發經驗的人，拿到 repository/ZIP 後只需要一個主要入口；但 AERIS 會明確區分 **INSTALLED** 與 **VERIFIED**，不會因 installer 結束就宣稱整間公司完成。

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

可選：

```powershell
.\INSTALL_AERIS_LOCAL.ps1 -Mode offline
.\INSTALL_AERIS_LOCAL.ps1 -LocalModel qwen3:4b-instruct
.\INSTALL_AERIS_LOCAL.ps1 -SkipCoreSync
.\INSTALL_AERIS_LOCAL.ps1 -SkipLocalModelInstall
```

`-Skip*` 只用於 CI、已預先配置的機器或受控維修情境；使用後不得宣稱完整 local/offline continuity 已驗證。

Windows installer 會：

1. 找 Python，並硬性確認版本 >= 3.10；
2. 建立 `.venv`；
3. online 時同步 read-only Core，offline bundle 可從 `portable_assets/core-reference` 還原；
4. 優先使用有 `.sha256` sidecar 的 staged Ollama installer，否則使用 winget；
5. 安裝/確認 local model；
6. 建立 machine report / Knowledge DB；
7. 跑 unit/security tests；
8. 驗證 100-role company manifest；
9. 跑 doctor；
10. local runtime/model 未完成且不是 Human 明確 skip 時，installer 以失敗結束。

## Linux / Jetson

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

支援 apt/dnf/yum/pacman/zypper 的基礎 prerequisite 安裝，並硬性確認 Python >= 3.10。

Local runtime 安裝優先順序：

1. `portable_assets/installers/ollama-install.sh` + 必須存在並吻合的 `.sha256` sidecar；
2. 若沒有 staged installer，才從精確官方 HTTPS URL `https://ollama.com/install.sh` 取得。

線上取得的 installer 會保存下載來源、時間與 SHA-256 provenance；這是 **TLS transport + recorded hash**，不是 upstream signature/pinned digest，因此不得描述成 cryptographically pinned supply chain。

CI 可使用：

```bash
AERIS_SKIP_CORE_SYNC=1 AERIS_SKIP_LOCAL_RUNTIME_INSTALL=1 bash ./INSTALL_AERIS_LOCAL.sh auto
```

這只測 installer kernel，不代表 Ollama/model clean install 已驗證。

## Default local model

目前 continuity baseline：

```text
qwen3:4b-instruct
```

原因：本 repo 需要可本地運行、Ollama 有正式 tag、且目前官方模型資料標示 Apache-2.0 的 baseline。**每次商用 release 前仍要重新確認實際 model/tag/license；模型不是 AERIS 身份，也不是 100-seat capability 的證明。**

## Core reference

Online 安裝會執行 `scripts/sync-core.*`：

```text
0_JN1_AERIS/main
→ local .aeris/core-reference
→ detached origin/main
→ push URL DISABLED
→ pre-push DENY
→ SHA recorded
```

Air-gapped fresh machine 若無法連 GitHub，必須在離線包中預先帶入：

```text
portable_assets/core-reference/
```

否則 Knowledge DB 只能索引 implementation 本身，不能聲稱已載入 canonical Core。

## 安裝後一定要做 real-machine acceptance

Windows：

```powershell
.\scripts\local-acceptance.ps1
```

Linux / Jetson：

```bash
bash scripts/local-acceptance.sh
```

此步會做真實 local inference 與 offline-mode inference。沒有這個 evidence，只能標 `INSTALLED / NOT_VERIFIED`。

## Hard offline

斷開或阻擋 external network 後：

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

或：

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

這才是 HARD OFFLINE acceptance。詳細見 `docs/security/LOCAL_NETWORK_ENFORCEMENT.md`。

## Air-gapped asset requirements

完全斷網的新機器至少必須事先準備：

- implementation source/package；
- Python >= 3.10 或合法離線 installer；
- local inference runtime；
- selected model weights/model store；
- Core snapshot；
- intended workflow 所需 Skills/Methods/data；
- 必要 driver / proprietary tool / license / calibration assets。

這些資產是否可搬遷必須符合各自 license/公司政策。

## 私有公司狀態

Software ZIP 不包含 `.env/.aeris/data/logs/portable_assets`。Memory/Knowledge/Evidence/customer data 等私有狀態使用：

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
```

需要 `age`。詳見 `docs/deployment/STATE_BACKUP_RESTORE.md`。

## 最低驗收

```bash
python -m aeris_runtime company status
python -m aeris_runtime machine detect --write
python -m aeris_runtime knowledge build
python -m aeris_runtime knowledge stats
python -m aeris_runtime doctor
```

再加 `scripts/local-acceptance.*` 才能從 installed 升級到 real-machine verified scope。
