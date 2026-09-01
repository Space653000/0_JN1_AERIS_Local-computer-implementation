# AERIS Local Verification SOP — 給沒有開發經驗的使用者

這份 SOP 的目的不是讓安裝看起來成功，而是回答：**這一台電腦上的 AERIS 到底真正能做什麼？**

GitHub/CI 無法替你的實體電腦證明 GPU、驅動、模型、網路隔離、COMSOL/APx/KLIPPEL、校正或客戶資料環境。這些必須在目的機器留下 evidence。

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

---

## 1. Windows：一般安裝

在 implementation repo 根目錄開 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

安裝完成後執行：

```powershell
.\scripts\local-acceptance.ps1
```

必須產生：

```text
.aeris/state/LOCAL_ACCEPTANCE.json
```

它會驗：

- Company manifest / 100-seat registry；
- repository unit/security tests；
- Knowledge build；
- Supported Machine Profile；
- canonical Core cache integrity；
- Local AI doctor；
- 真實 local inference；
- offline mode doctor；
- 真實 offline-mode inference。

任何一步失敗：**這台機器不能標 VERIFIED。**

---

## 2. Linux / Jetson

```bash
bash ./INSTALL_AERIS_LOCAL.sh
bash ./scripts/local-acceptance.sh
```

Jetson 額外必須人工記錄並測試：

- JetPack / L4T 版本；
- power mode / clocks；
- RAM 使用量；
- swap 是否使用；
- local inference latency；
- 連續負載 thermal / throttling；
- reboot 後 Ollama/AERIS 是否能恢復；
- hard-offline inference。

沒有這些證據，Jetson 只能叫 `IMPLEMENTED / NOT_VERIFIED`。

---

## 3. HARD OFFLINE

最可信的驗收方法是先真的切斷外網：

- 拔掉 Ethernet；
- 關閉 Wi-Fi；
- 或使用經 Human 審核、可回復的 deny-all external-egress firewall/network policy。

Windows：

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

Linux / Jetson：

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

目前 acceptance 會探測多個 IPv4、DNS/TCP 與 IPv6 路徑。任何一條外網探針成功即 FAIL。

成功狀態名稱刻意是：

```text
OUTBOUND_PROBES_BLOCKED_NOT_GLOBAL_PROOF
```

因為有限探針不是數學證明「整台 OS 的任何 process 永遠不可能外流」。若案件需要更高保密，使用 air-gap 或獨立 Private AERIS Zone。

---

## 4. 完全斷網的新電腦需要先準備什麼？

Air-gap bundle 至少需要與目的機器相容的：

```text
implementation software image
+ canonical Core snapshot
+ Python/runtime prerequisite
+ Ollama/inference runtime installer
+ local model asset
+ intended Skills/Methods/data
+ required drivers
+ proprietary tool/license/calibration assets（如適用）
```

### Windows staged Python

目前 installer 支援：

```text
portable_assets/installers/python-3.11-amd64.exe
portable_assets/installers/python-3.11-amd64.exe.sha256
```

SHA-256 不吻合直接 BLOCK。

### Staged Ollama

Windows：

```text
portable_assets/installers/OllamaSetup.exe
portable_assets/installers/OllamaSetup.exe.sha256
```

Linux/Jetson：

```text
portable_assets/installers/ollama-install.sh
portable_assets/installers/ollama-install.sh.sha256
```

注意：某個 installer 是否真的支援該 OS/version/silent switch，仍以該版本供應商文件與目的機器 E2E 為準。

### Staged GGUF model

```text
portable_assets/models/
├─ model.manifest.json
└─ <model>.gguf
```

範例 manifest：

```json
{
  "schema_version": 1,
  "model_name": "qwen3:4b-instruct",
  "format": "gguf",
  "file": "model.gguf",
  "sha256": "<actual-file-sha256>"
}
```

Installer 會先驗 SHA-256，再用 Ollama `create` 匯入。沒有 staged model 且沒有已安裝 model 時，`offline` 安裝直接 BLOCK，不允許偷偷上網 pull。

Linux/Jetson 的 Python portable runtime 與 glibc/architecture/distro 關係複雜，**沒有宣稱一個 Python binary 可以跑所有 Linux/Jetson**。如果目的機器沒有相容 Python >=3.10，必須為該 Machine Profile 預先準備合法、相容的 runtime/套件。

---

## 5. 建立可驗證的 Core air-gap snapshot

在一台已連網、已同步 canonical Core 的 AERIS 機器：

```bash
python -m aeris_runtime core snapshot --output portable_assets/core-reference
```

它建立：

```text
CORE_SNAPSHOT_MANIFEST.json
+ Core files
+ 每檔 SHA-256
+ canonical Core SHA
```

目的機器執行：

```bash
python -m aeris_runtime core verify
```

任何 missing/extra/tampered file 都應 FAIL。

若使用 Git cache，則必須驗證 push URL disabled + deny pre-push hook。

---

## 6. Public Internet 資料進 AERIS

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

Human 明確批准：

```bash
python -m aeris_runtime ingress-approve ".aeris/ingress/quarantine/<id>"
```

若本機沒有 scanner，必須人工評估後才可刻意使用 `--allow-unscanned`。若有 content-risk marker，必須人工評估後使用 `--acknowledge-content-risk`。這兩個參數代表 **Human 接受剩餘風險**，不是系統證明內容安全。

---

## 7. Cloud AI

Cloud 是明確的 `public research` channel，不是私人公司資料通道。

Private engineering：

```bash
python -m aeris_runtime chat "..."
```

固定走 Local AI。

Public research：

```bash
python -m aeris_runtime research "公開問題"
```

AERIS 不會自動附加 local Memory / Evidence / files / customer data；但你自己輸入的 query 文字會送到 Cloud，因此**不要把任何私密內容貼到 research**。

Cloud credential 優先使用 process environment 或：

```text
AERIS_CLOUD_API_KEY_FILE=<local secret file path>
```

不要把 key commit 到 Git、放雲端同步資料夾、寫進公開 log。

---

## 8. 專業工具驗收

每個工具分開驗，不可因軟體「有安裝」就標 adapter VERIFIED。

### MATLAB / COMSOL

至少記錄：

- exact version/build；
- license status；
- API/Engine/LiveLink 可用；
- AERIS adapter version；
- deterministic test input；
- deterministic/expected output；
- run log/hash；
- failure/timeout/rollback behavior。

### APx / KLIPPEL / SoundCheck / ACQUA

再加：

- hardware serial/model；
- driver/firmware；
- fixture；
- calibration status/date；
- sample rate/channel/measurement condition；
- raw measurement artifact；
- known reference/golden result。

只有 E2E + calibration/evidence PASS 才能叫 VERIFIED。

---

## 9. 公司搬家驗收

真正搬家不是只有 ZIP。

```text
Software Image
+ Encrypted Private State
+ Private Asset Pack
→ destination restore
→ Core verify
→ company status
→ unit/security tests
→ Knowledge build
→ real local inference
→ offline inference
→ intended tool/calibration acceptance
→ LOCAL_ACCEPTANCE.json
```

Software image 裡有 `release-metadata/`：

- `SBOM.spdx.json`
- `PROVENANCE.json`
- `SHA256SUMS`

傳輸後先驗 checksum，再執行安裝。

Private state 使用 `age`：

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
python scripts/private-state.py import private-backups/AERIS-private-state.age
```

Restore 後一定重新跑 acceptance。

---

## 10. 最終可以說什麼？

只有 Evidence 支援的 scope 才能說 VERIFIED。

推薦格式：

```text
AERIS instance: VERIFIED for <capability list>
Implementation commit: <SHA>
Canonical Core SHA: <SHA>
Machine profile: <profile>
OS / architecture: <version>
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
所有網路資料都可以下載
有 CI 綠燈所以整間公司完成
```

這就是 AERIS 的可靠性文化：**指定環境、指定能力、指定證據、指定限制。**
