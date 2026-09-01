# AERIS One-Click Installation — PRE-ALPHA

目標：讓沒有開發經驗的人使用單一入口完成**可自動化的安裝工作**；但 AERIS 永遠區分 `INSTALLED`、`TESTED`、`VERIFIED`。Installer 結束不等於整間 100-seat 聲學工程公司完成。

Canonical design authority：read-only `Space653000/0_JN1_AERIS@main`。

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

常用選項：

```powershell
.\INSTALL_AERIS_LOCAL.ps1 -Mode offline
.\INSTALL_AERIS_LOCAL.ps1 -LocalModel qwen3:4b-instruct
.\INSTALL_AERIS_LOCAL.ps1 -SkipCoreSync
.\INSTALL_AERIS_LOCAL.ps1 -SkipLocalModelInstall
```

`-Skip*` 只適用 CI、已預先配置的機器或受控維修；使用後不得宣稱完整 local/offline continuity 已驗證。

Windows installer 會：

1. 找 Python 並確認 >= 3.10；
2. 若無 Python，可使用 checksum-verified staged Python installer 或 online winget；
3. 建立 `.venv`；
4. 同步 read-only Core，或從 staged Core snapshot/cache 還原；
5. 安裝/確認 Ollama；offline 時只接受預先存在或真正 staged 的本機資產，不以 silent network fallback 假裝成功；
6. 安裝/匯入 local model；
7. 寫入 requested `AERIS_LOCAL_MODEL`；
8. 建立 Machine / Knowledge 狀態；
9. 跑 unit/security tests、company manifest、doctor；
10. 明確要求後續 real-machine acceptance。

## Linux / Jetson

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

Online 可依支援 distro 使用 package manager，並在需要時取得 Ollama 官方 HTTPS bootstrap installer。

### 重要：`ollama-install.sh` 不是 air-gap package

官方型 `ollama-install.sh` 是 bootstrap/network installer。即使把 shell script 本身 stage 到：

```text
portable_assets/installers/ollama-install.sh
```

也**不能**因此宣稱 clean-machine offline install 已成立。

AERIS 現在採 fail-closed：

- `Mode=offline` 且 Ollama 不存在 → **BLOCKED**；
- offline 不執行 `ollama-install.sh`；
- 先在連網/受控環境安裝 Ollama，再斷網，或等待/建立經真機驗證的 machine-specific self-contained runtime package。

這是刻意保守，而不是功能退步：**不能把會偷偷抓網路資產的 bootstrap script 包裝成離線 installer。**

## Local private-provider network scope

預設：

```text
AERIS_LOCAL_NETWORK_SCOPE=loopback
AERIS_LOCAL_BASE_URL=http://127.0.0.1:11434
```

Private engineering 只接受 loopback。

若 Human 明確使用受控 LAN inference node：

```text
AERIS_LOCAL_NETWORK_SCOPE=trusted_lan
AERIS_LOCAL_BASE_URL=http://192.168.1.20:11434
```

`trusted_lan` 只接受 literal RFC1918 / IPv6 ULA / loopback IP。Public/global IP 與任意 hostname 都被拒絕，避免把 public endpoint 誤叫「LOCAL ONLY」。

## Default local model

目前 continuity baseline：

```text
qwen3:4b-instruct
```

模型只是可替換算力，不是 AERIS identity，也不是 100-seat 專業能力證據。實際商用/formal release 前仍需重新確認 exact model/tag/digest/license 及真機 performance。

## Core reference

Online sync：

```text
0_JN1_AERIS/main
→ local .aeris/core-reference
→ detached HEAD at reviewed origin/main
→ canonical fetch URL
→ disabled push URL
→ deny pre-push
→ recorded Core SHA
```

`python -m aeris_runtime core verify` 對 Git cache 會確認：

- canonical fetch URL；
- disabled push URL；
- deny hook；
- detached HEAD；
- `HEAD == origin/main == recorded SHA`；
- working tree clean。

Air-gap snapshot：

```bash
python -m aeris_runtime core snapshot --output portable_assets/core-reference
```

Snapshot 會保存 exact file inventory + per-file SHA-256 + Core SHA。目的地再執行：

```bash
python -m aeris_runtime core verify
```

注意：未簽章的 hash manifest 提供**相對於可信 manifest 的 integrity**，不是 source authenticity。高保證 release/relocation 仍需 signing/attestation。

## Model assets

目前 staged GGUF model 可使用 `portable_assets/models/model.manifest.json` 指定 model name/file/SHA-256 後由 Ollama import。

這只處理 model asset；**不代表 Linux/Jetson Ollama runtime 本身已經有通用 self-contained offline package**。

## 安裝後一定要 real-machine acceptance

Windows：

```powershell
.\scripts\local-acceptance.ps1
```

Linux / Jetson：

```bash
bash scripts/local-acceptance.sh
```

驗收至少包含：

```text
Company Manifest / 100-seat registry
Unit + security tests
Knowledge build
Machine Profile
Core integrity
Local provider endpoint policy
Local doctor
REAL local inference
Offline-mode doctor
REAL offline-mode inference
```

沒有 `.aeris/state/LOCAL_ACCEPTANCE.json` evidence，只能叫 `INSTALLED / NOT_VERIFIED`。

## Hard Offline

先物理斷網或套用受控 outbound deny，再跑：

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

或：

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

成功後的精確語意是：**測試的 outbound probes 被阻擋且 local/offline inference 成功**。這仍不是數學證明任意 process/firmware 永遠沒有其他 egress path。

## Portable company image

Software package 故意不包含 `.env`、private state、model weights、客戶資料、license/credential。

每個 software package 內有：

```text
release-metadata/SBOM.spdx.json
release-metadata/PROVENANCE.json
release-metadata/SHA256SUMS
```

package 外另產生：

```text
<package>.sha256
```

它可驗 transfer integrity；Production authenticity/signing/attestation 尚未完成，不得因有 SHA-256 就宣稱 signed release。

## 私有公司狀態

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
```

使用外部 `age`；AERIS 不自製弱加密替代品。完整搬家仍需：

```text
Software Image
+ Encrypted Private State
+ legal Human-controlled Private Asset Pack
+ destination restore
+ real tool/calibration acceptance
+ local acceptance evidence
```

## 真正的 AERIS 核心還沒因安裝器完成而完成

Core P0 仍要求後續優先落實：

```text
task_id / engineering state
Evidence Bundle
Independent Verification
G0–G5
Golden failure cases
Audit
Health / expected-run monitoring
Skills / Methods / Standards
```

因此 One-Click 的定義是「一鍵建立目前可用且可誠實驗收的 AERIS kernel」，不是「按一下就憑空取得已驗證的 100 位世界級聲學工程師」。
