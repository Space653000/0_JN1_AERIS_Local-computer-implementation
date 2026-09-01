# AERIS Portable Company Kernel — PRE-ALPHA

> **AERIS — Acoustic Engineering & Research Intelligence System**  
> 將 AERIS 的公司軟體、治理、執行核心與工程信任機制部署到明確支援的本機；不把「安裝完成」誤寫成「100 位成熟工程師／公司完成」。

Canonical read-only Core: `https://github.com/Space653000/0_JN1_AERIS`

## 1. 人類只需要給 Codex 三個輸入

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
<LOCAL_TARGET_PATH>
```

在具備 GitHub + terminal 權限的 Codex 環境中，repository contract 要求 Codex 自動：

```text
讀 Core 權限/順序
→ 安全取得 Implementation 到指定路徑
→ 偵測/盤點機器
→ 安裝/設定可安全自動化的依賴
→ 驗 Core read-only cache
→ local model / Knowledge
→ unit/security tests
→ 真機 local/offline acceptance
→ scope-bound 公司開幕
→ loopback supervisor + heartbeat
→ Evidence/Audit handoff
→ 交給 Claude Code 獨立驗收
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

> Repository 可以把流程做到極度自動化，但不能繞過 OS 權限、EULA/license、credential、實體線材/治具/校正、或外部 agent host 沒有授權 terminal/network 的現實限制。遇到這些才是合法 Human Gate。

## 2. 人與 AI 的責任分離

```text
Human Chief Engineer = final authority
Core                 = design authority
Codex                = primary local executor / installer / implementer
Claude Code          = independent reviewer / acceptance auditor
Evidence             = engineering decision basis
```

Codex 不自我認證。安裝/開幕後 Claude Code 自動檢查：

```powershell
# Windows
.\CLAUDE_VERIFY_AERIS.ps1
```

```bash
# Linux / Jetson
bash ./CLAUDE_VERIFY_AERIS.sh
```

Claude 預設只 review，不安裝、不靜默修、不改 Core、不為了過關改 privacy。若找到缺陷：`FAIL/BLOCKED → separate repair → fresh review`。

Implementation-side reviewer contract：[`CLAUDE.md`](CLAUDE.md)

## 3. 兩個 GitHub 的權責

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

Normal deployment 不寫兩個 GitHub。若 Human 明確要求 Implementation development，才走 branch → CI → PR → protected main。Canonical Core 的 publication 另屬 Human-controlled governance process。

`core.lock.json` 與 `config/core_alignment.json` 鎖定已審查的 Core SHA。Core 一旦改變，remote drift gate 應先 FAIL，不能自動改 lock 讓 CI 變綠。

## 4. AERIS 中心思想

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

Permanent truth:

```text
Model != Identity
Memory != Evidence
Execution != Completion
Dashboard != Truth
Agent consensus != engineering truth
Implemented != Tested != Verified
```

## 5. Company Opening 不等於 Installer PASS

Operational states：

```text
CLOSED
BOOTSTRAPPING
BLOCKED
OPEN_WITH_LIMITS
OPEN_VERIFIED_SCOPE
```

目前 `OPEN_VERIFIED_SCOPE` 唯一允許的 baseline scope 是：

```text
LOCAL_PORTABLE_COMPANY_KERNEL_BASELINE
```

而且必須有真機 `LOCAL_ACCEPTANCE.json` PASS。即便 kernel scope 開幕，`company_complete` 仍是 `false`，未完成的聲學 P0/Skills/Methods/Standards/tool adapters 必須繼續顯示。

CI 只可產生：

```text
CI_SMOKE_PASS_NOT_REAL_OPENING
```

絕不能拿 CI smoke 冒充真機開幕。

## 6. 本機 Evidence / State

Autopilot：

```text
.aeris/state/AUTOPILOT_PREFLIGHT.json
.aeris/state/AUTOPILOT_RESULT.json
.aeris/state/DEPLOYMENT_REPORT.json
.aeris/state/LOCAL_ACCEPTANCE.json
.aeris/state/COMPANY_OPENING.json
.aeris/state/HEARTBEAT.json
.aeris/state/SUPERVISOR.json
```

Claude：

```text
.aeris/state/CLAUDE_TESTS.json
.aeris/state/CLAUDE_ACCEPTANCE.json
.aeris/state/claude-unit-tests.log
.aeris/state/claude-core-drift.log
.aeris/state/claude-review.log
```

Engineering trust baseline：

```text
.aeris/tasks/<task_id>/task.json
.aeris/evidence/<run_id>/...
.aeris/verification/<task_id>/gates.json
.aeris/audit/audit.jsonl
```

Application hash chains/hashes provide deterministic tamper detection relative to their local manifests/chains; they are not WORM storage or external signing/attestation.

## 7. P0 Trust primitives 已有可執行 baseline

目前 branch/版本中的 baseline 機制包括：

- task identity + guarded state machine：`DRAFT → READY → EXECUTING → EXECUTED → EVIDENCED → VERIFIED → APPROVED → RELEASED`，禁止跳關；
- failure states；
- Evidence Bundle create/seal/verify + per-file SHA-256；
- G0 Contract / G1 Numerical / G2 Domain / G3 Regression / G4 Independent Review / G5 Approval structured records；
- G4 reviewer independence guard；
- G5 `Human Chief Engineer` authority guard；
- R0–R4 machine-readable authority policy；
- hash-chained application audit ledger；
- scope-bound company opening；
- loopback-only supervisor/heartbeat；
- deterministic Claude acceptance aggregator。

這些是 **trust mechanism baseline**，不是「完整聲學公司已完成」。Golden acoustic datasets、成熟 Skills/Methods/Standards、Dynamic Pod execution、reproduction runner、完整 professional tool adapters 等仍依 `config/maturity.json` 判定。

## 8. R0–R4 權限

Machine-readable：[`config/risk_authority.json`](config/risk_authority.json)

```text
R0 = read-only low-risk
R1 = reversible local change + tests
R2 = controlled execution + preconditions + independent review
R3 = high-impact/destructive + independent review + Human approval
R4 = external/formal/customer/production/Core publication + independent review + Human approval
```

AI 永遠不能 self-authorize R3/R4；G5 PASS 需要 Human Chief Engineer + evidence reference。

## 9. Private engineering 的 Local 有真實 endpoint 邊界

Default：

```text
AERIS_LOCAL_NETWORK_SCOPE=loopback
AERIS_LOCAL_BASE_URL=http://127.0.0.1:11434
```

受控 LAN 必須 Human 明確 opt-in，且只接受 literal RFC1918 / IPv6 ULA / loopback IP。Public/global endpoint 或任意 hostname 不能被 private router 冒充 Local。

Cloud 是明確 `public research` channel；不自動附加 local files / Memory / Evidence / customer/project / measurement/CAE/factory data。

Application privacy 不等於 OS/firmware 全宇宙零外流證明。

## 10. Offline truth

Software `mode=offline` ≠ air gap。

Real-machine acceptance 會實際跑 local inference 與 offline-mode inference。Hard Offline 必須另外切斷/阻擋外網並跑 probe。

Linux/Jetson 的 `ollama-install.sh` bootstrap 不是 self-contained air-gap runtime package；缺真正 offline prerequisite 時要 BLOCK，不准偷偷下載。

## 11. Local supervisor

開幕後 supervisor 只 bind：

```text
127.0.0.1:8765
```

Endpoints：

```text
GET  /health
GET  /status
POST /shutdown  # local token required
```

`/health` 只代表 supervisor service liveness + projected opening state，**不是整間公司 HEALTHY 的證明**。

CLI：

```bash
python -m aeris_runtime company supervisor-status
python -m aeris_runtime company stop-supervisor
```

## 12. Engineering task / Evidence example

```bash
python -m aeris_runtime task create "Validate microphone array performance" --actor Codex --risk R1
python -m aeris_runtime evidence create <task_id> --actor Codex
python -m aeris_runtime evidence seal <run_id> --actor Codex
python -m aeris_runtime evidence verify <run_id>
python -m aeris_runtime verify record <task_id> G0_CONTRACT PASS --reviewer reviewer --evidence evidence://<run_id>
```

AI 不可直接從 `EXECUTED` 跳成 `VERIFIED/APPROVED/RELEASED`。

## 13. Knowledge / Public ingress

Local Knowledge 目前是 self-cleaning SQLite text index，FTS5 available 時使用 FTS；不是完整世界級 Acoustic Knowledge System。

Public URL：public-IP validation → pinned/TLS connection → redirect validation → quarantine → SHA-256 → local malware scan when available → content risk flags → Human promotion。下載/approve 都不代表 factual Canonical Knowledge。

## 14. Portable software != full company relocation

Software package 有 SBOM / provenance / internal checksums + external package `.sha256`，但 external hash 不是 signer identity。Private state、model weights、licenses、drivers、calibration、credentials 是獨立 Human-controlled assets。

Full relocation 必須 destination restore + Core verify + real-machine/tool/calibration acceptance。

## 15. Professional tools

COMSOL、MATLAB、APx、KLIPPEL、SoundCheck、ACQUA、Ansys、Simcenter 等仍須合法安裝、exact version、真正 adapter、E2E、硬體/校正/raw evidence 才能 VERIFIED。README 出現名字不等於 adapter。

## 16. 目前成熟度與下一步

Machine truth：[`config/maturity.json`](config/maturity.json)  
Reality audit：[`docs/AUDIT_REALITY_CHECK.md`](docs/AUDIT_REALITY_CHECK.md)  
Definition of Company Done：[`docs/DEFINITION_OF_COMPANY_DONE.md`](docs/DEFINITION_OF_COMPANY_DONE.md)

目前仍是 **PRE_ALPHA**。Autopilot 是 deployment/operations harness；真正主軸持續是：

```text
P0 trust baseline hardening
→ Golden acoustic cases
→ reproduction
→ mature Skills / Methods / Standards
→ professional acoustic corpus
→ executable role contracts
→ Dynamic Pods
→ professional tool adapters
→ mature control plane
```

**Implemented is not Verified. CI green is not Company Complete. Supervisor serving is not Company Healthy. Dashboard is not Truth.**
