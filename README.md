# AERIS Portable Company Kernel — PRE-ALPHA

> **GATE-06 RETRY R1 candidate — not accepted yet.** Frozen Blueprint:
> `v0.7.0-blueprint.1` → `64576bdbe680170fc1ea27306d1a2ab494cac733`.
> **PROJECT_IDENTIFICATION_ONLY**: two URLs do not authorize construction.
> Current Human authorization is compatibility/trust repair and Draft PR #33 only.
> No main merge, runtime cutover, E acceptance or new acoustic capability work.
> Older Full-Build instructions below are historical and do not override this gate.

**Implementation plan revision: v0.3.0-review.1** — [Execution plan](docs/IMPLEMENTATION_PLAN_V0_3.md) · [Audit findings](docs/reviews/ASTRA_REVIEW_20260907.md). Runtime package remains 0.2.0 / PRE_ALPHA. Known trust-chain defects are open; this documentation publication is not a runtime repair.

> **2026-09-07 審查優先：HOLD_FOR_SOL_RED_TEAM。** 先讀 [Astra → Sol → Astra 閘門](docs/ASTRA_SOL_REVIEW_GATE_V1.md)。下文 Full-Build／兩個 URL／缺口清零／續建命令只適用於閘門解除後的已授權有限批次。本次只修訂與發布文件；第 4 項等待使用者切換 GPT-5.6 Sol High，尚未執行本機總驗收。

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
→ 讀 Persistent Build Phases
→ 從第一個未完成階段續建
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

## 15.1 如何實際呼叫一位工程師（100 位聲學工程師之一）

上面第 15 節是底層的任務/證據 CLI。真正「請其中一位工程師做事」的入口是
`POST /api/v1/capabilities/execute`（本機伺服器啟動後，`127.0.0.1:8765` 上即可呼叫）。
下面是一個實際跑過、逐字可重現的範例：請 R095（供應商來料品質工程師）
對一批麥克風振膜的抽樣資料做允收篩選。

```bash
curl -s -X POST http://127.0.0.1:8765/api/v1/capabilities/execute \
  -H "Content-Type: application/json" \
  -d '{
    "role_id": "R095",
    "skill_id": "incoming-lot-sampling-screening-baseline",
    "objective": "Screen incoming microphone diaphragm lot #4471",
    "source_kind": "SYNTHETIC",
    "params": {
      "model": "SUPPLIED_INCOMING_LOT_SAMPLING_SCREEN",
      "source_kind": "MEASURED_INCOMING_INSPECTION",
      "sample_size": 200,
      "observed_nonconforming": 3,
      "confidence": 0.95,
      "max_acceptable_lot_fraction_nonconforming": 0.05
    }
  }'
```

回傳（節錄實際數值，非示意）：

```json
{
  "disposition": "BOUNDED_BASELINE_ACCEPT",
  "values": {
    "observed_fraction_nonconforming": 0.015,
    "one_sided_upper_fraction_nonconforming": 0.0383,
    "max_acceptable_lot_fraction_nonconforming": 0.05
  },
  "counter_hypotheses": [
    "Assembly/test-system variation rather than a true supplier lot shift",
    "Sampling variation at small sample size rather than a true elevated nonconforming rate"
  ],
  "next_discriminating_experiment": "INCREASE_INCOMING_SAMPLE_SIZE_WITH_MEASURED_INSPECTION_AND_SEPARATE_ASSEMBLY_TEST_SYSTEM_VARIATION_STUDY",
  "physical_measurement_verified": false,
  "professional_tool_verified": false,
  "truth": "Calculation completion is not role L3, physical acceptance, or product certification."
}
```

重點：
- `role_id`/`skill_id` 必須落在該角色的 `required_skills` 範圍內，否則直接拒絕
  （`"requested Skill outside this seat's contracted scope"`），不會靜默改路由。
- 回傳一定包含 `counter_hypotheses`（可能誤判成因）與
  `next_discriminating_experiment`（下一個能區分真假因的實驗），這是每個角色
  技能被要求誠實揭露不確定性的一部分，不是裝飾用欄位。
- `physical_measurement_verified: false` 誠實標示：這是本機自由基線計算，
  不等於已用專業儀器/校正流程驗證，也不是產品允收的最終人類核准。

**任何角色、任何技能都能這樣呼叫嗎？** 可以。這個 session 已對全部 100 席、
共 398 組「角色-技能」組合逐一呼叫 `factory.fixture_for(role_id, skill_id)`
生成範例輸入並執行，0 個錯誤（見 `docs/AERIS_P4_SKILL_TEACHING.md`）。想先看
某個角色某個技能的範例輸入長什麼樣，不想真的建任務，可以用唯讀端點：
`GET /api/v1/capabilities/fixture/{role_id}?skill={skill_id}`（`/services`
頁面的「能力矩陣」與 `/dashboard` 的 Skills Library 也是走這條路徑展示教學範例）。

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

## 20.5 存取控制：公開介紹頁 vs. 需登入的操作系統

只有 `/`（公開介紹頁）與 `/login` 對外開放；儀表板、工作區、進度中心、活動紀錄、服務頁與全部
`/api/v1/*` API 一律需要登入。首次使用請先在本機執行一次：

```bash
python -m aeris_runtime auth set-credentials
```

互動式輸入帳號密碼（`getpass`，畫面不回顯，也不會被記錄），僅將加鹽雜湊值存在本機
`.aeris/state/auth_credentials.json`（已被 `.gitignore` 排除，不會被提交）。這組帳密是**唯一的擁有者**，
擁有全部權限（包含管理其他帳號）；擁有者可以在 `/admin` 頁面（或 `auth grant-user` CLI 指令）新增授權
帳號，逐一勾選每個帳號能看到哪些頁面、能不能執行技能／建立任務，被授權的帳號永遠不能取得擁有者權限。
細節、session 生命週期與目前刻意尚未涵蓋的範圍（例如未來公開對外連線時的正式 HTTPS/反向代理）見
[`docs/AERIS_ACCESS_CONTROL.md`](docs/AERIS_ACCESS_CONTROL.md)。

## 21. Persistent Build Phases：換電腦不用重走聊天歷史

AERIS 後續建設不再依賴某一次 ChatGPT/Codex 對話內容。

正式續建索引：

- [`docs/AERIS_BUILD_PHASES.md`](docs/AERIS_BUILD_PHASES.md)
- [`config/build_phases.v1.json`](config/build_phases.v1.json)

已納入的正式階段：

1. [`AERIS LOCAL SOFTWARE COMPLETION PASS`](docs/AERIS_LOCAL_SOFTWARE_COMPLETION_PASS.md)
2. [`AERIS PROFESSIONAL COMPANY BUILD — 100-Engineer Capability Factory`](docs/AERIS_PROFESSIONAL_COMPANY_BUILD_100_ENGINEER_CAPABILITY_FACTORY.md)

未來每一次大型 AERIS 擴建提示詞都必須沉澱成新的 versioned Build Phase，並加入上述兩個索引。

因此未來任何支援電腦的正確流程是：

```text
選定唯一安全 local workspace
→ 貼兩個 GitHub URL
→ Codex 讀 Core + Implementation governance
→ 讀 Build Phase catalog
→ 查真實 local Evidence
→ 已完成且相容的 phase 直接略過
→ 從第一個未完成 phase 繼續
→ 不重新依聊天紀錄摸索整條建設路徑
```

這是 AERIS 的跨機器持久建設記憶。完成狀態仍只能由 Evidence 判定，不能由 AI 自述判定。

**Implemented is not Verified. CI green is not Company Complete. Supervisor serving is not Company Healthy. Dashboard is not Truth.**
