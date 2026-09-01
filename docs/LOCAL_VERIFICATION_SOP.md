# AERIS Local Verification SOP — 給沒有開發經驗的使用者

這份 SOP 的目的不是讓安裝看起來成功，而是回答：**這一台電腦上的 AERIS 到底真正能做什麼？**

GitHub/CI 無法替你的實體電腦證明 GPU、驅動、模型、網路隔離、COMSOL/APx/KLIPPEL、校正或客戶資料環境。這些必須在目的機器留下 Evidence。

## 0. 先理解三種不同狀態

```text
INSTALLED
= 檔案與 runtime 已部署

TESTED
= 自動測試通過

VERIFIED
= 這台真實電腦 / 真實工具 / 真實模型 / 真實安全模式完成驗收
```

看到 `PASS` 前不要自行把狀態升級。

## 1. Windows：一般安裝

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
.\scripts\local-acceptance.ps1
```

必須產生：

```text
.aeris/state/LOCAL_ACCEPTANCE.json
```

至少驗：Company manifest / 100-seat registry、unit/security tests、Knowledge、Machine Profile、canonical Core integrity、Local endpoint policy、Local doctor、real local inference、offline-mode inference。

任何一步失敗：**這台機器不能標 VERIFIED。**

## 2. Linux / Jetson

```bash
bash ./INSTALL_AERIS_LOCAL.sh
bash ./scripts/local-acceptance.sh
```

Jetson 額外必須人工記錄/驗證 JetPack/L4T、power mode、RAM/swap、inference latency、thermal/throttling、reboot recovery、hard-offline inference。沒有這些 Evidence，只能叫 `IMPLEMENTED / NOT_VERIFIED`。

## 3. Private engineering endpoint policy

預設：

```text
AERIS_LOCAL_NETWORK_SCOPE=loopback
AERIS_LOCAL_BASE_URL=http://127.0.0.1:11434
```

只接受 localhost / loopback。

若 Human 明確使用受控 LAN inference node：

```text
AERIS_LOCAL_NETWORK_SCOPE=trusted_lan
AERIS_LOCAL_BASE_URL=http://192.168.1.20:11434
```

`trusted_lan` 只接受 literal RFC1918 / IPv6 ULA / loopback IP。Public/global IP、任意 DNS hostname、embedded credentials 都拒絕。

這可以避免「程式叫它 Local，所以實際送到公網也算 Local」的假安全；但 trusted LAN 本身仍需你的網路分段、防火牆、必要時 TLS/ACL 與實機驗收。

## 4. HARD OFFLINE

最可信的驗收方法是先真的切斷外網：拔 Ethernet、關 Wi‑Fi，或使用 Human 審核、可回復的 deny-all external-egress policy。

Windows：

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

Linux / Jetson：

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

目前 acceptance 探測多個 IPv4、DNS/TCP 與 IPv6 路徑。任何一條成功即 FAIL。

成功狀態刻意叫：

```text
OUTBOUND_PROBES_BLOCKED_NOT_GLOBAL_PROOF
```

有限探針不是數學證明「整台 OS 的任何 process/firmware 永遠不可能外流」。高機密案件使用 air-gap 或獨立 Private AERIS Zone。

## 5. 完全斷網的新電腦需要先準備什麼？

```text
implementation software image
+ verified canonical Core cache/snapshot
+ Python/runtime prerequisite
+ local inference runtime already installed OR genuinely self-contained verified offline package
+ local model asset
+ intended Skills/Methods/data
+ required drivers
+ proprietary tool/license/calibration assets（如適用）
```

### Windows staged Python

```text
portable_assets/installers/python-3.11-amd64.exe
portable_assets/installers/python-3.11-amd64.exe.sha256
```

SHA-256 不吻合直接 BLOCK。

### Windows staged Ollama

```text
portable_assets/installers/OllamaSetup.exe
portable_assets/installers/OllamaSetup.exe.sha256
```

Silent-install switch、OS compatibility、供應商版本仍需目的機器 E2E。

### Linux / Jetson Ollama — 重要限制

不要把：

```text
portable_assets/installers/ollama-install.sh
```

當成完整 air-gap runtime。這類 script 是 bootstrap/network installer，可能再從網路抓真正 runtime 資產。

因此 `Mode=offline` 且機器沒有 Ollama 時，AERIS 現在直接 **BLOCKED**，不執行 bootstrap script。

目前正確 SOP：

```text
在受控/可連網階段把 Ollama 安裝並驗證好
→ 匯入/準備模型
→ 建 Core snapshot/private assets
→ 斷網
→ 再跑 Offline / Hard-Offline Acceptance
```

要做到真正「全新 Linux/Jetson 零網路一包裝好」，仍需建立**machine-specific self-contained Ollama/runtime package**、來源/授權/雜湊/簽章策略與真機 E2E；目前此能力在 `maturity.json` 明確為 `NOT_IMPLEMENTED`。

### Staged GGUF model

```text
portable_assets/models/
├─ model.manifest.json
└─ <model>.gguf
```

範例：

```json
{
  "schema_version": 1,
  "model_name": "qwen3:4b-instruct",
  "format": "gguf",
  "file": "model.gguf",
  "sha256": "<actual-file-sha256>"
}
```

Installer 先驗 SHA-256，再用 Ollama `create` 匯入。沒有 staged/installed model 時 offline 直接 BLOCK。

Linux/Jetson Python portable runtime 也受 architecture/glibc/distro 影響；AERIS 沒有宣稱一個 Python binary 可跑所有 Linux/Jetson。

## 6. Core 驗證

Online guarded Git Core cache 必須同時通過：

```text
origin fetch URL = canonical Core
origin push URL = DISABLED://...
pre-push hook = DENY
HEAD = detached
HEAD == origin/main == recorded core-target SHA
working tree = clean
```

執行：

```bash
python -m aeris_runtime core verify
```

這會抓出「本機 Core cache 被手動改過但 push guard 還在」的情況。

### Air-gap Core snapshot

在已同步且審查過 Core 的機器：

```bash
python -m aeris_runtime core snapshot --output portable_assets/core-reference
```

Snapshot 內容：

```text
CORE_SNAPSHOT_MANIFEST.json
+ Core files
+ exact file inventory
+ 每檔 SHA-256
+ canonical Core SHA
```

目的機再次：

```bash
python -m aeris_runtime core verify
```

missing/extra/tampered file 都應 FAIL。

**限制：**如果攻擊者能同時替換 snapshot 與 manifest，單純內部 hashes 不能證明 source authenticity。Production/high-assurance relocation 還需要 trusted/signed manifest/package attestation。

## 7. Public Internet 資料進 AERIS

下載不是信任。

```bash
python -m aeris_runtime ingress "https://public.example/file"
```

流程：

```text
public DNS/IP validation
→ pinned public-IP connection
→ TLS hostname validation
→ redirect re-validation
→ local quarantine
→ SHA-256
→ malware scanner（若本機有）
→ prompt-injection/content-risk markers
→ Human review
```

下載內容不會自動進 Knowledge。

Human 批准：

```bash
python -m aeris_runtime ingress-approve ".aeris/ingress/quarantine/<id>"
```

沒有 scanner 時使用 `--allow-unscanned`、有 content-risk marker 時使用 `--acknowledge-content-risk`，都代表 **Human 明確接受剩餘風險**，不是系統證明內容安全/正確。

## 8. Cloud AI

Cloud 是 `public research` channel，不是私人公司資料通道。

Private engineering：

```bash
python -m aeris_runtime chat "..."
```

固定走 endpoint-policy-compliant local/trusted-LAN AI。

Public research：

```bash
python -m aeris_runtime research "公開問題"
```

AERIS 不自動附加 local Memory / Evidence / files / customer data；但你自行輸入的 query 文字會送 Cloud，所以不要貼私密內容。

Cloud credential 優先使用 process environment 或：

```text
AERIS_CLOUD_API_KEY_FILE=<local secret file path>
```

## 9. 專業工具驗收

每個工具分開驗；「軟體有安裝」不等於 adapter VERIFIED。

MATLAB/COMSOL 至少記錄 exact version/build、license、API/Engine/LiveLink、adapter version、deterministic test input/output、run log/hash、failure/timeout/rollback。

APx/KLIPPEL/SoundCheck/ACQUA 再加 hardware serial/model、driver/firmware、fixture、calibration、sample rate/channel/condition、raw measurement、known reference/golden result。

只有 E2E + applicable calibration/evidence PASS 才叫 VERIFIED。

## 10. 公司搬家驗收

真正搬家不是只有 ZIP：

```text
Software Image
+ external <package>.sha256
+ SBOM / provenance
+ Encrypted Private State
+ Private Asset Pack
→ destination restore
→ Core verify
→ company status
→ unit/security tests
→ Knowledge build
→ real local/offline inference
→ intended tool/calibration acceptance
→ LOCAL_ACCEPTANCE.json
```

Software image 內：

- `release-metadata/SBOM.spdx.json`
- `release-metadata/PROVENANCE.json`
- `release-metadata/SHA256SUMS`

archive 外：

- `<package>.sha256`

External SHA-256 可驗 transfer integrity，但不證明 signer identity。Production signing/attestation 尚未實作。

Private state 使用 `age`：

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
python scripts/private-state.py import private-backups/AERIS-private-state.age
```

Restore 後一定重新跑 acceptance。

## 11. 最終可以說什麼？

只有 Evidence 支援的 scope 才能說 VERIFIED。

推薦格式：

```text
AERIS instance: VERIFIED for <capability list>
Implementation commit: <SHA>
Canonical Core SHA: <SHA>
Machine profile: <profile>
OS / architecture: <version>
Local endpoint scope: <loopback/trusted_lan>
Local model: <model/version/digest>
Security mode: <local/offline/hard-offline>
Tools verified: <exact list>
Acceptance artifact: .aeris/state/LOCAL_ACCEPTANCE.json
Known limitations: <list>
```

不要說：

```text
任何電腦都 100% 可用
100 位工程師全部完成
完全不可能外流
所有 Cloud AI 都支援
有 CI 綠燈所以整間公司完成
```

AERIS 的可靠性文化：**指定環境、指定能力、指定 Evidence、指定限制。**
