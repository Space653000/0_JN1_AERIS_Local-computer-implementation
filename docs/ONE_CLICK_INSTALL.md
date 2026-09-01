# AERIS One-Click Installation — PRE-ALPHA

目標：沒有開發經驗的人，拿到 repository / Software Image 後只有一個主要入口；但 AERIS 嚴格區分 **INSTALLED**、**TESTED**、**VERIFIED**，installer 結束不等於整間公司完成。

完整本機驗收請接著讀 [`LOCAL_VERIFICATION_SOP.md`](LOCAL_VERIFICATION_SOP.md)。

## 1. Windows

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

`-Skip*` 只用於 CI、已預先配置的機器或受控維修；使用後不得宣稱完整 local/offline continuity 已驗證。

Windows installer 會：

1. 找 Python，硬性確認 `>= 3.10`；
2. online 可用 winget；offline fresh machine 可使用 checksum-verifed staged Python；
3. 建立 `.venv`；
4. 把 `-LocalModel` 真正寫入 local runtime `.env`，避免 pull/doctor 使用不同模型；
5. online 同步 read-only Core，air-gap 可使用 checksum-manifested Core snapshot；
6. 安裝/確認 Ollama-compatible local runtime；
7. 優先使用已存在或 staged GGUF model；`offline` 不得因缺模型偷偷上網 pull；
8. 建立 Machine Report / Knowledge DB；
9. 跑 unit/security tests；
10. 驗證 Company Manifest / 100-seat registry；
11. 跑 doctor；
12. 缺少必要 local continuity dependency 且不是 Human 明確 skip 時，installer 以 BLOCK/FAIL 結束。

### Windows offline staged Python

```text
portable_assets/installers/python-3.11-amd64.exe
portable_assets/installers/python-3.11-amd64.exe.sha256
```

SHA-256 sidecar 必須與檔案吻合。實際 Python installer 版本/架構必須與目的 Windows 相容。

### Windows offline staged Ollama

```text
portable_assets/installers/OllamaSetup.exe
portable_assets/installers/OllamaSetup.exe.sha256
```

Installer 仍必須在真實 Windows 版本驗 silent install、啟動、reboot recovery；文件存在不等於 vendor installer 永遠維持同一參數。

---

## 2. Linux / Jetson

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

連網模式支援 apt/dnf/yum/pacman/zypper 的基礎 prerequisite 安裝；最後一定硬性確認可用 Python `>=3.10`。

Python resolver 會依序考慮：

```text
portable_assets/python/bin/python3
python3.13
python3.12
python3.11
python3
```

`portable_assets/python/bin/python3` **不是通用 Linux binary 承諾**。它必須由 Human 為該 OS/architecture/glibc/Machine Profile 準備相容 runtime。

若 `offline` 且沒有 Python >=3.10 或 venv support，直接 BLOCK；不會偷偷執行 package-manager 網路安裝。

### Linux / Jetson Ollama runtime

優先：

```text
portable_assets/installers/ollama-install.sh
portable_assets/installers/ollama-install.sh.sha256
```

若連網且沒有 staged installer，才允許從官方 HTTPS URL取得目前 installer。線上取得後保存 source/time/SHA-256 provenance；這只能稱為 **TLS transport + recorded hash**，不是 upstream signature 或 pinned vendor digest。

`offline` 時沒有 staged/preinstalled runtime 直接 BLOCK。

---

## 3. Offline staged GGUF model

Windows / Linux / Jetson 的 baseline offline importer 支援：

```text
portable_assets/models/
├─ model.manifest.json
└─ <model-file>.gguf
```

`model.manifest.json`：

```json
{
  "schema_version": 1,
  "model_name": "qwen3:4b-instruct",
  "format": "gguf",
  "file": "model.gguf",
  "sha256": "<actual-sha256>"
}
```

流程：

```text
model name must equal requested AERIS_LOCAL_MODEL
→ format must be gguf
→ file exists
→ SHA-256 matches
→ Ollama create
→ doctor
→ real inference during local acceptance
```

沒有 model、manifest/hash 錯誤、或 import/inference 失敗，都不可叫 offline ready。

---

## 4. Default local model

目前 continuity baseline：

```text
qwen3:4b-instruct
```

它是可替換的 local continuity/retrieval/reasoning baseline，**不是 100-seat professional capability 的證明**。商用/formal release 前重新確認 exact model/tag/digest/license。

---

## 5. Canonical Core reference

Online 安裝可執行 `scripts/sync-core.*`：

```text
0_JN1_AERIS/main
→ local .aeris/core-reference
→ detached origin/main
→ push URL DISABLED
→ pre-push DENY
→ Core SHA recorded
```

驗證：

```bash
python -m aeris_runtime core verify
```

### 建立 air-gap Core snapshot

在已同步並審查 Core 的連網機：

```bash
python -m aeris_runtime core snapshot --output portable_assets/core-reference
```

Snapshot 不帶 `.git`，而是帶：

```text
CORE_SNAPSHOT_MANIFEST.json
+ repository / branch / canonical Core SHA
+ exact file inventory
+ per-file SHA-256
```

目的機器 `core verify` 會拒絕 missing / extra / tampered file。

因此 air-gap fresh machine 不一定需要 Git，但一定需要可驗證 Core snapshot 或已受 guard 的 Git cache。

---

## 6. 安裝後一定要做 Real-Machine Acceptance

Windows：

```powershell
.\scripts\local-acceptance.ps1
```

Linux / Jetson：

```bash
bash scripts/local-acceptance.sh
```

它至少驗：

- Company Manifest；
- tests；
- self-cleaning Knowledge build；
- Supported Machine Profile；
- Core integrity；
- real local inference；
- real offline-mode inference。

沒有 `.aeris/state/LOCAL_ACCEPTANCE.json`，只能標 `INSTALLED / NOT_VERIFIED`。

---

## 7. HARD OFFLINE

先物理斷網或套用 Human 已審核的 external-egress deny policy，再跑：

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

或：

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

Acceptance 會做多 IPv4 / DNS+TCP / IPv6 outbound probes。任何探針成功即 FAIL。

全部被阻擋時，狀態刻意記為：

```text
OUTBOUND_PROBES_BLOCKED_NOT_GLOBAL_PROOF
```

有限探針不是數學證明所有 OS process/path 永遠無法外傳；最高敏感部署仍應使用 air-gap / private zone / OS firewall / least privilege / no-cloud-sync 等多層控制。

---

## 8. Public information ingress

Public URL 不是可信資料。

```bash
python -m aeris_runtime ingress "https://public.example/file"
```

現在流程：

```text
URL syntax/credential check
→ resolve all DNS answers
→ any non-public IP => DENY
→ connect directly to validated public IP
→ TLS SNI/certificate validates original hostname
→ redirect revalidate + repin
→ download size limit
→ local quarantine
→ SHA-256
→ local malware scanner if available
→ content/prompt-injection risk markers
→ Human promotion only
```

下載不會自動進 Knowledge。

```bash
python -m aeris_runtime ingress-approve ".aeris/ingress/quarantine/<id>"
```

沒有 clean malware scan 時，只有 Human 明確 review 後才能刻意 `--allow-unscanned`；有 content-risk marker 時同理需 `--acknowledge-content-risk`。這些旗標表示接受剩餘風險，不是「系統證明安全」。

---

## 9. Cloud credential

優先使用 process environment 或 local secret file：

```text
AERIS_CLOUD_API_KEY_FILE=<path outside Git/cloud-sync where practical>
```

`.env` 仍可支援相容性，但不應把 real API key commit 到 Git 或放入雲端同步目錄。

Cloud research 只接受 explicit public query；使用者自己輸入的 query 文字仍會送到 Cloud，因此 private data 必須留在 `aeris chat` / local tools。

---

## 10. Portable software image / provenance

打包：

```powershell
.\scripts\package-company.ps1
```

或：

```bash
bash scripts/package-company.sh
```

Software Image 故意排除 `.env/.aeris/data/logs/portable_assets/private-backups`。

每包包含：

```text
release-metadata/
├─ SBOM.spdx.json
├─ PROVENANCE.json
└─ SHA256SUMS
```

SPDX inventory 同時記 SHA-1（SPDX 2.3 Package Verification Code 所需）與 SHA-256；安全傳輸驗證使用 SHA-256。

這些 metadata 是 integrity/provenance 基礎，不等於 cryptographic signing/attestation。正式 release signing 仍是後續 gate。

---

## 11. Private company state

Software Image 不等於整間公司狀態。

Memory/Knowledge/Evidence/customer/local state 使用 `age`：

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
python scripts/private-state.py import private-backups/AERIS-private-state.age
```

Private-state archive 會拒絕 path traversal、symlink、hardlink、device、FIFO 等危險 member；restore 後仍必須重新跑 Local Acceptance。

---

## 12. 目前不允許的宣稱

即使 installer 正常結束，也不能說：

```text
100 位成熟聲學工程師完成
所有電腦都支援
所有 Cloud AI 都已整合
完全不可能資料外流
所有公開資料都安全可信
COMSOL/MATLAB/APx/KLIPPEL 已驗證
完整公司搬遷已驗證
```

真正判斷看 `config/maturity.json`、CI 與目的機器 Evidence。
