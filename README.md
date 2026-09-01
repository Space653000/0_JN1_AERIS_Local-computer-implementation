# AERIS Portable Company Kernel — PRE-ALPHA

> **AERIS — Acoustic Engineering & Research Intelligence System**  
> 把同一套 AERIS 公司軟體、制度與可攜式執行核心部署到明確支援且通過驗收的本機；不把「有架構」誤寫成「100 位成熟工程師已完成」。

Canonical design target / read-only SSOT:  
`https://github.com/Space653000/0_JN1_AERIS/tree/main`

## 1. 兩個 GitHub 的權責

```text
0_JN1_AERIS
= WHAT AERIS MUST BE
= READ-ONLY North Star / Architecture / Research / UI / Governance
               │
               │ read / fetch / compare only
               ▼
0_JN1_AERIS_Local-computer-implementation
= HOW AERIS IS CURRENTLY IMPLEMENTED AND DEPLOYED
= Portable Company Kernel / cloud construction site
               │
               │ branch → tests → PR → main
               ▼
profile-matched local machine
               │
               │ real-machine acceptance
               ▼
VERIFIED scope-specific AERIS instance
```

Codex/implementation 不得修改 canonical Core。若 implementation 與 Core 衝突，Core 勝出。

`core.lock.json` 鎖定已審查 Core SHA；CI 執行 read-only drift gate。Core 若由 Human 更新，implementation 應先 FAIL，直到新 Core 被重新審查、實作並刻意更新 lock/alignment contract。

## 2. AERIS 的中心思想

```text
1 Human Chief Engineer
+ 100 Virtual Acoustic Engineering capability seats
+ ordinary Temporary Pod 2–8 roles
+ complex Temporary Pod 5–15 roles
+ model-neutral compute
+ Skills / Methods / Standards / Workflows
+ real engineering tools
+ Evidence / Provenance
+ Independent Verification
+ Human Approval
+ Reproducibility
```

100 seats 是 capability/authority/evidence/review boundaries，不是 100 個常駐 LLM process。

Permanent truth rules：

```text
Model != Identity
Memory != Evidence
Execution != Completion
Dashboard != Truth
Agent consensus != engineering truth
Implemented != Tested != Verified
```

## 3. 目前成熟度

產品階段：**PRE_ALPHA**。

Machine-readable truth：[`config/maturity.json`](config/maturity.json)  
Core semantic invariants：[`config/core_alignment.json`](config/core_alignment.json)  
Reality audit：[`docs/AUDIT_REALITY_CHECK.md`](docs/AUDIT_REALITY_CHECK.md)  
Human–AI cooperation：[`docs/AI_HUMAN_RELIABILITY_CONTRACT.md`](docs/AI_HUMAN_RELIABILITY_CONTRACT.md)  
本機驗收：[`docs/LOCAL_VERIFICATION_SOP.md`](docs/LOCAL_VERIFICATION_SOP.md)

成熟度只允許：

```text
NOT_IMPLEMENTED
→ IMPLEMENTED
→ TESTED
→ VERIFIED
```

外部軟體/硬體條件可用 `BLOCKED_EXTERNAL`。

目前 deployment/privacy/portability kernel 已有相當多實作與 CI；但 Core P0 的 Task State、Evidence Bundle、G0–G5、Golden Cases、Audit、Health、Skills、Methods、Standards 等仍未完成。因此 **安全的 portable kernel != 完整 Acoustic Engineering Organization OS**。

## 4. 零經驗安裝入口

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

Linux / Jetson：

```bash
bash ./INSTALL_AERIS_LOCAL.sh
```

詳細：[`docs/ONE_CLICK_INSTALL.md`](docs/ONE_CLICK_INSTALL.md)

Installer 採 fail-closed：缺必要 offline asset 時 BLOCK，不偷偷連網、不把 skip 當 verified。

### Linux / Jetson air-gap 限制

`ollama-install.sh` 是 bootstrap/network installer，不是 self-contained offline runtime package。

因此 `Mode=offline` 且 Ollama 尚未存在時，installer 會 **BLOCK**，不執行 bootstrap script。真正 clean-machine air-gap Linux/Jetson runtime package 尚需 machine-specific implementation + real-machine verification。

## 5. Private engineering 的「Local」有網路邊界

預設：

```text
AERIS_LOCAL_NETWORK_SCOPE=loopback
AERIS_LOCAL_BASE_URL=http://127.0.0.1:11434
```

只准 localhost / loopback。

受控 LAN inference node 必須由 Human 明確 opt-in：

```text
AERIS_LOCAL_NETWORK_SCOPE=trusted_lan
AERIS_LOCAL_BASE_URL=http://192.168.x.x:11434
```

`trusted_lan` 只接受 literal RFC1918 / IPv6 ULA / loopback IP。Public/global IP 與任意 hostname 不可被 private router 當作「LOCAL」。

Private engineering 在 `offline/local/cloud/auto` 四種 mode 都不會因 mode 本身被送到 public Cloud AI。

## 6. Cloud 是公開研究通道，不是私有工程 fallback

```text
PUBLIC RESEARCH ONLY
        │
        ├─ local/offline → local AI
        ├─ cloud → configured cloud; optional local fallback
        └─ auto → local first, cloud when allowed/needed
```

AERIS 不自動附加：

- local files;
- Memory;
- Evidence;
- customer/project data;
- measurement/CAE/factory data;
- private history。

Best-effort DLP 不能保證零 false negative；Human 仍要把 research channel 當成公開通道。

## 7. Public ingress 是 Quarantine，不是 Knowledge

```text
Public URL
→ public-IP validation
→ pinned connection + TLS hostname validation
→ redirect revalidation
→ QUARANTINE
→ SHA-256
→ local malware scan if available
→ content/prompt-injection risk flags
→ explicit Human promotion
```

即使 Human approve，也不等於 factual truth、legal reuse 或 Canonical Knowledge。

## 8. Core cache 必須驗內容，不只驗「不能 push」

Online guarded Git cache：

```text
canonical fetch URL
+ disabled push URL
+ deny pre-push
+ detached HEAD
+ HEAD == origin/main == recorded Core SHA
+ clean working tree
```

驗證：

```bash
python -m aeris_runtime core verify
```

Air-gap snapshot：

```bash
python -m aeris_runtime core snapshot --output portable_assets/core-reference
```

會保存 exact file list + SHA-256 + reviewed Core SHA。注意：未簽章 manifest 只提供相對 integrity；source authenticity/signing 仍是後續 production gate。

## 9. 安裝完成 != 本機 VERIFIED

Windows：

```powershell
.\scripts\local-acceptance.ps1
```

Linux / Jetson：

```bash
bash scripts/local-acceptance.sh
```

驗：Company Manifest、unit/security、Knowledge、Machine Profile、Core integrity、Local doctor、real local inference、offline-mode inference 等。

Evidence：

```text
.aeris/state/LOCAL_ACCEPTANCE.json
```

Hard Offline：

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

或：

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

正確結論只能是「測試的 outbound paths 被阻擋」，不能宣稱數學證明任何 OS/process/firmware 永遠無 egress。

## 10. 100-seat organization

Registry：[`company/organization/roles.v1.json`](company/organization/roles.v1.json)

角色只有在具備並通過以下條件後，才可從 defined seat 升級成 verified capability：

```text
Role Contract
+ Skills
+ Methods
+ Tool Permissions
+ Required Evidence
+ Golden / Negative / Regression tests
+ Acceptance Rubric
+ Independent Review
```

目前 `100_role_executable_contracts` 仍未完成。

## 11. Local Knowledge

目前是 self-cleaning local SQLite text index，FTS5 available 時使用 FTS；不是完整世界級 Acoustic Knowledge System。

```bash
python -m aeris_runtime knowledge build
python -m aeris_runtime knowledge stats
python -m aeris_runtime knowledge search "beamforming"
```

Permanent Knowledge 未來必須走：

```text
Finding
→ Verified Finding
→ Lesson Candidate
→ Engineering Review
→ Canonical Knowledge
```

## 12. Portable software != full company relocation

Software package 故意排除 private state / secrets / model weights / proprietary assets。

Package 內：

```text
release-metadata/SBOM.spdx.json
release-metadata/PROVENANCE.json
release-metadata/SHA256SUMS
```

Package 外：

```text
<package>.sha256
```

SHA-256 可驗 transfer integrity，但不是 signer identity。Production signing/attestation 仍未實作。

Private state 使用：

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
```

完整搬家 = Software Image + Encrypted Private State + legal Private Asset Pack + destination/tool/calibration/local acceptance。

## 13. Professional tools

COMSOL、MATLAB、APx、KLIPPEL、SoundCheck、ACQUA、Ansys、Simcenter、driver/license/hardware 不因 README 出現就算 adapter。

每個 tool 必須 legal install + exact version + adapter + E2E + applicable calibration/raw evidence 後才能 VERIFIED。

## 14. 下一個主軸：回到 Core P0

Deployment/security hardening 已達到能支撐後續工程的程度。接下來核心優先順序應是：

```text
task_id / state machine
→ Evidence Bundle
→ Verification G0–G5
→ independent review / Human approval records
→ Golden acoustic cases
→ Audit / Health
→ Skills / Methods / Standards
→ Dynamic Pod
→ professional tools
→ mature live control plane
```

不要再把大量時間只花在 installer/UI polish 而讓 Evidence/Verification 落後。

## 15. 核心真值

```text
Core GitHub
= AERIS 應該成為什麼

Implementation GitHub
= AERIS 目前真正實作到哪裡、如何部署

Local runtime / Evidence
= 某一台機器與某一次工程工作真正發生了什麼
```

**Implemented is not Verified. CI green is not Company Complete. Dashboard is not Truth. Memory is not Evidence. Execution is not Completion.**
