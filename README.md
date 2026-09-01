# AERIS Portable Company Kernel — PRE-ALPHA

> **AERIS — Acoustic Engineering & Research Intelligence System**  
> 將 AERIS 的公司軟體、治理、執行核心與工程信任機制部署到明確支援的本機；不把「安裝完成」誤寫成「100 位成熟工程師／公司完成」。

Canonical read-only Core: `https://github.com/Space653000/0_JN1_AERIS`

## 1. 正常 Full-Build：選好資料夾後只貼兩個 URL

如果 Codex 已經開啟／選取**唯一且安全、可寫入的目標 workspace**，例如 `C:\0_JN1_AERIS\`，then **two URLs are the complete Full-Build trigger**：

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
```

不需要再貼第二份長提示詞、不需要 plan confirmation，也不需要再輸入 local path。只有「沒有安全目標」或「同時有多個可能目標」時，Codex 才應要求最小必要的 path clarification。

Repository contract 要求 Codex 自動執行：

```text
讀 Core / Implementation governance
→ 取得最新 CI-passed Implementation
→ gap inventory
→ 關閉安全、zero-cost、software-only gaps
→ machine inventory + qualification baseline
→ 安裝/設定可安全自動化的 zero-cost prerequisites
→ 驗證 Core read-only cache
→ local model + Knowledge
→ unit/security/trust/acoustic regression
→ 真機 local/offline acceptance
→ scope-bound 公司開幕
→ loopback supervisor + heartbeat
→ persistence/watchdog
→ Evidence/Audit handoff
```

Codex 主入口：

```powershell
# Windows
.\AERIS_AUTOPILOT.ps1
```

```bash
# Linux / Jetson
bash ./AERIS_AUTOPILOT.sh
```

完整 SOP：[`docs/AUTOPILOT_ZERO_TOUCH_SOP.md`](docs/AUTOPILOT_ZERO_TOUCH_SOP.md)

## 2. Default deployment = zero-cost / no-Claude

Default profile：`AERIS-ZERO-COST-NO-CLAUDE-V1`。

- **Claude Code is optional**；不是 default opening prerequisite，也不會由 Autopilot 預設啟動。
- **No Claude token is required**。
- 不要求 paid cloud API。
- 不要求購買、安裝或啟用 COMSOL / MATLAB / APx / KLIPPEL / SoundCheck / ACQUA 等付費專業軟體才能完成 default opening。
- 不自動接受 package/source/license/EULA agreement；需要明確接受時 fail closed 到 Human Gate。
- Independent review 的核心是 reviewer identity/context/permission separation，不是綁定特定外部模型。

Optional Claude wrapper 仍保留給明確需要的獨立 reviewer path：

```powershell
.\CLAUDE_VERIFY_AERIS.ps1
```

```bash
bash ./CLAUDE_VERIFY_AERIS.sh
```

CI 對這些 wrapper 的 smoke 明確是 **no Claude/token invocation**。

Policy：[`docs/ZERO_COST_NO_CLAUDE_DEPLOYMENT.md`](docs/ZERO_COST_NO_CLAUDE_DEPLOYMENT.md)

## 3. 人、Core、Codex、Evidence 的權責

```text
Human Chief Engineer = final authority for high-impact / formal release
Core                 = read-only design authority / WHAT
Codex                = primary local executor / installer / repairer
Reviewer allocator   = independent-review seat/context/permission separation baseline
Evidence             = engineering decision basis
```

Canonical Core 不由 Implementation/Codex 寫入。Implementation 走 branch → deterministic test → Windows+Ubuntu PR CI → merge → post-merge main CI。

## 4. 兩個 GitHub 的權責

```text
0_JN1_AERIS
= WHAT AERIS MUST BE
= READ-ONLY Core / North Star / Architecture / Governance
             │ read / fetch / compare
             ▼
0_JN1_AERIS_Local-computer-implementation
= HOW AERIS IS EXECUTED
= Portable Company Image
             │ local Autopilot
             ▼
profile-matched local machine
             │ real-machine acceptance
             ▼
OPEN_VERIFIED_SCOPE for an explicitly named scope
```

`core.lock.json`、`config/core_alignment.json`、Autopilot、company manifest 與 maturity Core truth 必須鎖定相同 reviewed Core SHA。Core 一旦 drift，CI 要先 FAIL；不准自動改 lock 假裝一致。

## 5. AERIS 中心思想

```text
1 Human Chief Engineer
+ 100 Virtual Acoustic Engineering capability seats
+ ordinary Temporary Pod 2–8 roles
+ complex Temporary Pod 5–15 roles
+ model-neutral compute
+ Skills / Methods / Standards / Workflows
+ engineering tools
+ Evidence / Provenance
+ Independent Verification
+ Human Approval
+ Reproducibility
```

Permanent truth：

```text
Model != Identity
Memory != Evidence
Execution != Completion
Dashboard != Truth
Agent consensus != engineering truth
Implemented != Tested != Verified
```

## 6. Company Opening 不等於 Installer PASS

Operational states：

```text
CLOSED
BOOTSTRAPPING
BLOCKED
OPEN_WITH_LIMITS
OPEN_VERIFIED_SCOPE
```

目前 baseline opening scope：

```text
LOCAL_PORTABLE_COMPANY_KERNEL_BASELINE
```

必須有真機 `LOCAL_ACCEPTANCE.json` PASS。即使 kernel scope 開幕，`company_complete` 仍不得因此變成 `true`。

CI 只能產生 CI-scope evidence，不能冒充真機 opening。

## 7. Current TESTED cloud/software baselines

目前已有 executable/tested baseline 的重要能力包括：

- task identity + guarded engineering state machine；
- Evidence Bundle integrity；
- G0–G5 structured verification records；
- R0–R4 authority policy；
- append-only hash-chained audit ledger；
- task-aware independent reviewer-seat allocation；
- 100-seat callable + machine-readable baseline contract framework；
- deterministic Dynamic Pod planner；
- expected-run health monitor + watchdog baseline；
- deterministic reproduction runner；
- evidence-grounded role claim guard；
- local Dashboard / Workspace / Services control plane；
- real-browser semantic E2E on Windows 2025 + Ubuntu 24.04；
- deterministic machine resource qualification baseline；
- SHA-256-pinned acoustic Golden regression baseline；
- first deterministic acoustic Skills / Methods / workflow slice；
- Standards Registry metadata baseline；
- local SQLite/FTS Knowledge baseline；
- zero-cost/no-Claude default deployment policy；
- Windows Store-alias Python resolver and fail-closed zero-cost winget regression；
- portable package + SBOM/provenance + external SHA-256 sidecar。

這些只代表明確 automated scope 的 `TESTED`，不是全公司 `VERIFIED`。

## 8. 仍未完成、不可灌水的範圍

以下 broad/full scope 仍應保持未完成或 external blocked：

- 100-seat **完整 domain-executable contracts**；
- production-complete Speaker/Microphone Golden Dataset；
- broad mature Skills / Methods libraries；
- full live licensed/legal Standards corpus；
- professional acoustic corpus；
- pixel visual regression / full accessibility regression；
- production sustained machine qualification（driver/runtime/latency/thermal/load）；
- pre-login/system-service operation；
- OS-wide egress/DLP enforcement；
- self-contained Linux/Jetson air-gap local-model runtime package；
- release signing / attestation；
- full company relocation；
- commercial release readiness；
- proprietary professional-tool adapters without exact licensed/hardware/calibration Evidence。

Machine truth：[`config/maturity.json`](config/maturity.json)

## 9. Machine qualification baseline ≠ real-machine VERIFIED

`config/machine_qualification.v1.json` + `aeris_runtime/machine_qualification.py` deterministically inspect supported profile, RAM, free disk, Python, required tools, NVIDIA identity and VRAM where applicable。

可能狀態：

```text
QUALIFIED_BASELINE
NOT_QUALIFIED
BLOCKED_INCOMPLETE_EVIDENCE
NOT_APPLICABLE
```

`QUALIFIED_BASELINE` 不證明 sustained load、latency、thermal headroom、實際 driver/runtime compatibility、reboot recovery、hard-offline、instrument/license/calibration readiness。

## 10. Acoustic Golden regression baseline ≠ 完整 Golden Dataset

`golden/acoustics/v1/manifest.json` 現在已有 SHA-256-pinned deterministic cases：

- valid measurement import；
- deterministic FR analysis；
- passing requirement case；
- deliberately failing regression case；
- duplicate-frequency rejection。

這是 regression baseline，不是 production-complete Speaker/Microphone Golden Dataset。產品、transducer、fixture、chamber、direction、distance、noise、language、tolerance、uncertainty、calibration 等仍需 reviewed provenance + 真實工程 Evidence。

## 11. Browser E2E truth

Windows 2025 / Ubuntu 24.04 CI 使用真實 installed Chrome/Chromium/Edge headless browser，載入 `/`、`/workspace`、`/services`，執行 SPA JavaScript 並驗證 active view。

這是 semantic browser E2E，不是 pixel visual regression。Accessibility/visual regression 仍是獨立未完成 scope。

## 12. Private engineering 的 Local boundary

Default：

```text
AERIS_LOCAL_NETWORK_SCOPE=loopback
AERIS_LOCAL_BASE_URL=http://127.0.0.1:11434
```

受控 LAN 必須明確 opt-in，且只接受 policy 定義的 local/private literal IP。Public/global endpoint 或 arbitrary hostname 不能冒充 private Local provider。

Cloud 是明確 public-research channel；不自動附加 local files / Memory / Evidence / customer/project/measurement/CAE/factory data。

Application privacy 不等於 OS/firmware 全宇宙零外流證明。

## 13. Offline truth

Software `mode=offline` ≠ air gap。

Real-machine acceptance 必須實際跑 local inference 與 offline-mode inference。Hard Offline 另需阻斷外網並做 outbound probes / OS network review。

Linux/Jetson 的 `ollama-install.sh` bootstrap 不是 self-contained air-gap runtime package；缺真正 offline prerequisite 時要 BLOCK，不准偷偷下載。

## 14. Local supervisor / persistence

開幕後 supervisor 只 bind loopback，例如：

```text
127.0.0.1:8765
```

`/health` 代表 service liveness + scoped opening projection，不是整間公司 HEALTHY。

CLI：

```bash
python -m aeris_runtime company supervisor-status
python -m aeris_runtime company stop-supervisor
```

Windows current-user Scheduled Task / fallback 與 Linux/Jetson user persistence 已有 implementation baseline，但要到真正 target 上完成 sign-out/reboot/watchdog Evidence 才能升級。

## 15. Engineering task / Evidence example

```bash
python -m aeris_runtime task create "Validate microphone array performance" --actor Codex --risk R1
python -m aeris_runtime evidence create <task_id> --actor Codex
python -m aeris_runtime evidence seal <run_id> --actor Codex
python -m aeris_runtime evidence verify <run_id>
python -m aeris_runtime verify record <task_id> G0_CONTRACT PASS --reviewer reviewer --evidence evidence://<run_id>
```

AI 不可直接從 `EXECUTED` 跳成 `VERIFIED/APPROVED/RELEASED`。

## 16. Knowledge / Public ingress

Local Knowledge 是 self-cleaning SQLite text/FTS baseline，不是完整 professional acoustic corpus。

Public ingress：public target validation → pinned/TLS connection → redirect revalidation → quarantine → SHA-256 → local malware scan when available → content risk flags → explicit Human promotion。Download/promote 都不等於 factual Canonical Knowledge。

## 17. Portable software != full company relocation

Software package 有 SBOM / provenance / internal checksums + external package `.sha256`。External hash 是 transfer-integrity evidence，不是 signer identity。

Private state、model weights、licenses、drivers、calibration、credentials 是獨立 Human-controlled assets。Full relocation 仍需 destination restore + Core verify + real-machine/tool/calibration acceptance。

## 18. Professional tools

COMSOL、MATLAB、APx、KLIPPEL、SoundCheck、ACQUA 等仍是 `BLOCKED_EXTERNAL`，直到 exact licensed version、真正 adapter、E2E、硬體/校正/raw Evidence 齊全。README 出現名字、偵測到 executable 或有 public API 文件都不等於 verified adapter。

## 19. AI change acceptance

任何 cloud-reproducible defect 的 closure contract：

```text
branch
→ deterministic regression test/gate
→ Windows 2025 + Ubuntu 24.04 PR CI
→ merge
→ post-merge main Windows + Ubuntu CI
```

只有之後真正需要 target machine 的項目，才交給一次必要的 local acceptance cycle。這是避免本機 Codex 重複修已能在 GitHub 解決問題的主要 token-control 原則。

Protocol：[`docs/AI_CHANGE_ACCEPTANCE_PROTOCOL.md`](docs/AI_CHANGE_ACCEPTANCE_PROTOCOL.md)

## 20. 目前成熟度與下一階段

Reality audit：[`docs/AUDIT_REALITY_CHECK.md`](docs/AUDIT_REALITY_CHECK.md)  
Definition of Company Done：[`docs/DEFINITION_OF_COMPANY_DONE.md`](docs/DEFINITION_OF_COMPANY_DONE.md)

目前仍是 **PRE_ALPHA**。正確演進順序是：

```text
cloud/software trust baselines closed
→ one selected-machine acceptance cycle
→ real local/offline/persistence/reboot evidence
→ expand Golden + Skills + Methods + Standards + corpus
→ mature 100-seat domain contracts / Pods
→ optional licensed tool adapters as environments become available
→ signed/attested release + formal Human approval
```

**Implemented is not Verified. CI green is not Company Complete. Supervisor serving is not Company Healthy. Dashboard is not Truth.**
