# AERIS Reality Check / Anti-Fantasy Audit

**Status date:** 2026-09-01 (Asia/Taipei)  
**Applies to:** `Space653000/0_JN1_AERIS_Local-computer-implementation`  
**Canonical design authority:** read-only `Space653000/0_JN1_AERIS@main`  
**Reviewed Core SHA:** `bde158944ac21f076f39894600e172136c3a8c5a`  
**Implementation evidence baseline:** `bfacc5a5dd1ab07dee3d09286bcb59cccb558633`  
**Repair evidence:** PR #2 CI run 104 = SUCCESS; post-merge main CI run 105 = SUCCESS

## 1. Non-negotiable truth rule

```text
NOT_IMPLEMENTED → IMPLEMENTED → TESTED → VERIFIED
```

External dependencies may use `BLOCKED_EXTERNAL`.

- `IMPLEMENTED` = code/config exists.
- `TESTED` = automated tests exercise the stated contract and pass.
- `VERIFIED` = required real-machine / real-tool / real-evidence acceptance passes for a specified configuration.
- CI green proves only the exact CI scope.
- A 100-seat registry means capability slots, not 100 mature engineers.
- A secure installer does not substitute for an Evidence/Verification engineering system.

Machine-readable truth: `config/maturity.json`.

## 2. Fourth-audit Core-alignment conclusion

The implementation remains aligned with the canonical Core center philosophy:

```text
1 Human Chief Engineer
+ 100 capability seats, not 100 persistent agents
+ ordinary pod 2–8 / complex pod 5–15
+ model-neutral compute
+ local-first / offline continuity
+ Memory != Evidence
+ Execution != Completion
+ Evidence / Verification / Reproducibility
+ Human authority for high-impact release
```

The audit found real drift/holes rather than declaring everything fine. They were repaired through PR #2, whose Windows and Ubuntu CI passed, then squash-merged; the resulting `main` commit `bfacc5a5...` passed post-merge main CI run 105.

Automated-tested repairs now include:

1. implementation Constitution preserves Core mic-algorithm validation axes `noise / distance / azimuth / speaker / language`;
2. machine-readable Core semantic alignment is tied to `core.lock.json` reviewed Core SHA;
3. ordinary pod `2–8` and complex pod `5–15` are preserved;
4. guarded Git Core-cache verification checks canonical fetch URL, disabled push URL, deny hook, detached HEAD, clean worktree and `HEAD == origin/main == recorded SHA`;
5. private engineering rejects public/global endpoints and arbitrary hostnames; default is loopback, explicit trusted-LAN accepts only literal RFC1918/ULA/loopback IP;
6. `AERIS_CLOUD_FALLBACK_TO_LOCAL` is honored for the public-research channel;
7. Linux/Jetson offline mode does not execute `ollama-install.sh` as though it were a self-contained air-gap runtime package;
8. doctor readiness is scope-bound (`KERNEL_*_NOT_COMPANY_COMPLETE`) rather than generic whole-company `READY`;
9. quarantine Human-promotion code has positive and rejection test coverage;
10. portable archives emit external `.sha256` transfer-integrity sidecars and CI verifies them.

These automated contracts are `TESTED`, not real-machine `VERIFIED`.

## 3. Current automated kernel evidence

Post-merge main run 105 passed the exact CI scope on Windows and Ubuntu, including:

- compile and unit/security tests;
- Core semantic alignment and Core-cache tamper tests;
- private provider endpoint-policy tests;
- ingress/archive security tests;
- 100-seat manifest validation;
- canonical Core remote drift gate;
- Knowledge rebuild;
- machine-profile detection;
- mode switching;
- scoped doctor behavior;
- installer smoke with external local-AI installation deliberately skipped;
- SPDX/provenance generation;
- Windows/Linux portable package + external digest smoke.

This does **not** prove clean-machine installation, real GPU/Jetson behavior, hard network isolation, professional instruments, calibration, full relocation or Company Done.

## 4. Main strategic risk: Core P0 trust foundation is still missing

Canonical Core prioritizes trust infrastructure before mature autonomy. The implementation now has a stronger deployment/privacy/portability kernel, but these central AERIS capabilities remain materially absent:

- task identity and formal engineering state machine;
- machine-enforced STOP/ASK/REROUTE/VERIFY contract;
- Evidence Bundle engine;
- G0–G5 verification engine;
- independent reviewer allocation;
- R0–R4 authority/approval records;
- Golden acoustic failure/regression cases;
- append-only audit ledger;
- expected-run/health monitor;
- production Skills library;
- deterministic Methods library;
- live Standards Registry/lifecycle checks;
- professional acoustic corpus and reviewed knowledge-promotion workflow.

Therefore the next major development priority should pivot from mostly installer/security polish to the Core P0 engineering-trust foundation. Otherwise AERIS risks becoming a well-protected portable AI shell rather than the intended Acoustic Engineering Organization OS.

## 5. Core repository and local-cache boundary

Canonical Core is never written by implementation/Codex. `core.lock.json` matches the reviewed Core main SHA, and remote drift CI is read-only.

Local Core representations are either:

- guarded Git cache; or
- checksum-manifested air-gap snapshot.

Git cache now must pass canonical fetch URL, disabled push, deny hook, detached HEAD, clean worktree and `HEAD == origin/main == recorded Core SHA`.

Snapshot exact-file hashes provide integrity relative to the trusted manifest. They do **not** prove source authenticity if an attacker can replace both snapshot and manifest. High-assurance release/relocation still needs trusted signing/attestation.

## 6. GitHub server-side governance

Active Rulesets exist on both repositories; deletion/non-fast-forward are blocked, PR is required, and no bypass actor is configured.

Observed remaining governance gap:

- required approving review count = 0;
- no CODEOWNER review requirement;
- required AERIS CI status checks are not yet encoded in the Ruleset itself.

For implementation `main`, required Windows/Ubuntu AERIS CI checks are strongly recommended. For a solo-owned Core, Human review-count policy must avoid creating an impossible self-deadlock while still preventing AI bypass.

## 7. Privacy boundary

Private engineering endpoint policy:

```text
loopback (default)
OR
explicit trusted_lan + literal RFC1918/ULA/loopback IP
```

A global/public IP or arbitrary hostname is rejected as a private local provider. Public Cloud AI is available only through the explicit public-research channel, which does not automatically attach Memory/Evidence/customer files.

This is an application boundary, not proof that unrelated software, compromised OS/firmware or an authorized Human can never exfiltrate data. Strong deployments still require firewall/process/filesystem isolation or air gap.

## 8. Public ingress boundary

```text
public DNS/IP validation
→ connect pinned to validated public IP
→ TLS hostname verification
→ redirect revalidation
→ quarantine
→ SHA-256
→ local malware scan when available
→ content/prompt-injection risk markers
→ explicit Human promotion
```

This does not prove downloaded information is true, legally reusable or malware-free. Human-approved public ingress is still not automatically Canonical Knowledge.

## 9. Offline truth

Software `mode=offline` is not an air gap.

A clean Linux/Jetson machine with no Ollama cannot be made genuinely offline merely by staging `ollama-install.sh`; the repaired installer blocks that case. A true clean-machine air-gap runtime package for Linux/Jetson remains `NOT_IMPLEMENTED`.

A machine/workflow is not `OFFLINE VERIFIED` until required local dependencies exist, Core verifies, real local/offline inference passes and applicable Hard Offline/network Evidence is retained.

## 10. Supported-machine truth

A profile match is not full resource qualification. `machine_resource_qualification` remains unfinished: profile-specific OS/version/RAM/free-disk/accelerator/latency/headroom acceptance still needs a formal gate.

## 11. Knowledge truth

Current SQLite/FTS baseline is a self-cleaning local text index, not the final professional acoustic Knowledge System.

Canonical knowledge must eventually follow a reviewed promotion path such as:

```text
Observation
→ Finding
→ Verified Finding
→ Lesson Candidate
→ Engineering Review
→ Canonical Knowledge
```

LLM inference must not directly overwrite permanent engineering knowledge.

## 12. Professional tools

COMSOL, MATLAB, APx, KLIPPEL, SoundCheck, ACQUA, Ansys and Simcenter remain external/licensed dependencies. A README, detected executable or public API description is not an adapter.

`VERIFIED` requires the exact installed/versioned environment, implemented adapter, E2E execution and applicable hardware/calibration/raw Evidence.

## 13. Canonical Core internal consistency note for Human publication

One Core policy area should eventually be consolidated by Human-controlled Core publication:

- the Master Baseline risk section describes R0–R3;
- the later Web UI / Control Plane baseline defines R0–R4, including R4 formal/customer release.

Implementation follows the later R0–R4 control-plane model because it is more explicit for formal release. This is not permission for implementation to rewrite Core; Core should eventually expose one canonical machine-readable Risk Policy.

## 14. Relocation / supply-chain truth

A complete move is not one ZIP:

```text
Software Image
+ external package digest
+ SBOM / provenance
+ Encrypted Private State
+ legal Human-controlled Private Asset Pack
+ trusted source/signing policy where required
+ destination restore
+ real-machine/tool/calibration acceptance
```

External `.sha256` proves transfer integrity against the sidecar; it does not establish signer identity. Release signing/attestation remains `NOT_IMPLEMENTED`.

## 15. Still not a completed professional acoustic company

The implementation remains **PRE_ALPHA**. It is not legitimate to claim:

- `100 ENGINEERS READY`;
- complete Skills/Methods/Standards;
- production Dynamic Pod;
- complete Evidence/G0–G5;
- verified professional-tool adapters;
- absolute OS-wide zero egress;
- all computers/all AI providers supported;
- clean-machine Windows/Linux/Jetson verified;
- full-company relocation verified;
- production/commercial release ready;
- guaranteed revenue/profit.

## 16. Final fourth-audit conclusion

No examined AERIS north-star requirement requires fictional physics or a nonexistent category of software. The architecture is engineering-feasible **as a staged system with explicit supported configurations and external dependencies**.

That does not mean every target is implemented today, nor can arbitrary hardware/provider/tool/data be guaranteed universally compatible.

The valid definition of "100%" is narrower and testable:

> For one explicitly specified AERIS configuration and workflow, every required gate must produce Evidence and pass before that scope is called VERIFIED.

That is the standard this repository enforces.
