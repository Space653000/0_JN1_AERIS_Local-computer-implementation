# AERIS Reality Check / Anti-Fantasy Audit

**Status date:** 2026-09-01 (Asia/Taipei)  
**Applies to:** `Space653000/0_JN1_AERIS_Local-computer-implementation`  
**Canonical design authority:** read-only `Space653000/0_JN1_AERIS@main`  
**Reviewed Core SHA:** `82f4554623b2d87185dac39a3b93194af7dd5275`

Machine-readable truth remains `config/maturity.json`. This document is a human-readable audit boundary; it must never override the machine-readable state or turn CI evidence into real-machine evidence.

## 1. Non-negotiable truth rule

```text
NOT_IMPLEMENTED → IMPLEMENTED → TESTED → VERIFIED
```

External/Human boundaries use `HUMAN_GATE`, `EXTERNAL_LICENSE`, `PHYSICAL_HARDWARE`, or `REBOOT_LOGOFF_REQUIRED`.

- `IMPLEMENTED` = code/config exists but required acceptance evidence is still missing.
- `TESTED` = automated tests exercise the explicitly stated scope and pass.
- `VERIFIED` = the required real-machine / real-tool / physical / license / calibration evidence exists for an explicitly named configuration and scope.
- CI green proves only the exact CI scope.
- A 100-seat registry or baseline contract framework is not 100 domain-verified engineers.
- A deterministic Golden regression baseline is not a production-complete Speaker/Microphone Golden Dataset.

## 2. Current Core / governance truth

Canonical Core `main` is reviewed at:

```text
82f4554623b2d87185dac39a3b93194af7dd5275
```

Implementation `core.lock.json`, Core alignment, Autopilot and company truth must remain identical to that SHA. Remote Core drift is a hard CI gate; implementation must not silently rewrite the Core lock merely to make CI green.

Both repositories currently have active default-branch Rulesets that block deletion/non-fast-forward and require PRs, with no bypass actor. Required Human approval count and required AERIS CI checks are not encoded as strongly as the target policy; `docs/HUMAN_GITHUB_PROTECTION_REQUIRED.md` records that separate governance improvement. This does not permit bypassing the existing Rulesets.

## 3. Core P0 trust foundation has executable TESTED baselines

The earlier audit statement that the Core P0 trust foundation was materially absent is obsolete. Current automated baselines include:

- task identity and guarded engineering state machine;
- Evidence Bundle creation/sealing/integrity checks;
- structured G0–G5 verification records and authority boundaries;
- R0–R4 risk/approval policy with Human Chief Engineer authority for high-impact release;
- append-only hash-chained audit ledger;
- task-aware independent reviewer-seat allocation with identity/context/permission separation;
- deterministic Dynamic Pod baseline;
- expected-run health monitoring and watchdog baseline;
- deterministic reproduction runner;
- evidence-grounded role-output claim guard against fabricated measured/verified facts;
- same-origin local control plane, callable 100-seat baseline and real-browser semantic E2E;
- deterministic machine resource qualification baseline;
- versioned acoustic Golden regression baseline;
- first deterministic acoustic Skills, Methods and workflow slice;
- Standards Registry metadata baseline;
- local Knowledge SQLite/FTS baseline;
- zero-cost/no-Claude default deployment policy and fail-closed Windows bootstrap policy.

These are TESTED baselines only. They do not establish whole-company maturity, production completeness or real-machine VERIFIED status.

## 4. 100-seat truth

PR #20 added a machine-readable baseline role-contract framework and task-aware reviewer candidates for all 100 capability seats. The framework can be TESTED while the broad capability remains incomplete.

The local executable contract/free-baseline software is complete; independent specialty approval remains:

```text
100_role_executable_domain_contracts = HUMAN_GATE
```

A fully mature seat still needs domain-specific Skills, Methods, standards/tool permissions, evidence rubrics, Golden/negative/regression tests and independent review. A callable seat is not a human-equivalent verified acoustic engineer.

## 5. Machine qualification truth

A deterministic machine qualification engine now evaluates supported profile, RAM, free disk, Python, required tools, NVIDIA identity and VRAM where applicable. This baseline is TESTED in Windows/Ubuntu CI and fails closed on incomplete evidence.

That does **not** prove sustained inference stability, latency, thermal headroom, driver/runtime compatibility on the actual target, reboot recovery or hard-offline operation. Therefore the production/sustained `machine_resource_qualification` capability remains incomplete until the real target machine supplies that Evidence.

## 6. Acoustic Golden truth

`golden/acoustics/v1/manifest.json` is a versioned SHA-256-pinned deterministic regression baseline. It currently covers valid measurement import, deterministic FR analysis, a passing requirement case, an intentionally failing regression case and malformed duplicate-frequency rejection.

That automated baseline is `TESTED`. The production-complete Speaker/Microphone Golden Dataset is `PHYSICAL_HARDWARE` because it requires real product/transducer/fixture/chamber/direction/distance/noise/tolerance/calibration evidence and reviewed provenance.

## 7. Browser/UI truth

Real installed Chrome/Chromium/Edge headless semantic E2E runs on Windows 2025 and Ubuntu 24.04, loads Dashboard / Workspace / Services, executes the SPA and verifies the intended active view. That semantic baseline is TESTED.

Fixed-viewport dark/light screenshot and accessibility regression is TESTED for the same browser/environment. It is not a cross-version or cross-browser pixel-golden guarantee.

## 8. Zero-cost / no-Claude default truth

The default Full-Build path is bound to `AERIS-ZERO-COST-NO-CLAUDE-V1`.

For the default opening path:

- Claude Code is not required or launched;
- no Claude token is required;
- no paid professional software is required;
- no paid cloud API is required;
- third-party package/source/license/EULA acceptance is never silently auto-accepted;
- Windows bootstrap fails closed if a zero-cost prerequisite installation fails or requires a Human Gate.

Independent review is an authority/context-separation requirement, not a Claude dependency. The Claude verification wrappers remain optional tools and their CI smoke explicitly does not invoke Claude or consume a token.

## 9. Two-URL Full-Build trigger

When Codex already has exactly one safe selected writable workspace, the two canonical URLs are the complete Full-Build trigger. A second long prompt is not required. The local target path is requested only when no safe target exists or multiple targets are ambiguous.

The software-only closure loop is:

```text
latest CI-passed Core + Implementation
→ gap inventory
→ safe zero-cost software repair
→ deterministic regression gate
→ Windows 2025 + Ubuntu 24.04 PR CI
→ merge
→ post-merge main Windows + Ubuntu CI
→ one necessary real-machine acceptance cycle
```

## 10. Remaining legitimate Human/external/domain gates

The following are deliberately **not** upgraded merely because adjacent baselines exist:

- full 100-seat executable domain contracts;
- production-complete Speaker/Microphone Golden Dataset;
- broad mature Skills and Methods libraries;
- full live licensed/legal standards corpus and professional acoustic corpus;
- cross-browser/cross-version release-matrix acceptance;
- pre-login/system-service deployment mode;
- OS-wide network egress/DLP enforcement;
- self-contained Linux/Jetson air-gap local-model runtime package;
- trusted release signing/attestation;
- full-company relocation acceptance;
- commercial release readiness.

All purely local software items in the current Completion Pass are closed before release of its report. These remaining items require new Human authority, external rights, physical evidence, or reboot/logoff proof.

## 11. Real-machine acceptance remains a separate gate

Cloud CI cannot prove the user workstation or Jetson. `IMPLEMENTED` real-machine capabilities still require the actual target for evidence such as:

- fresh Windows/Linux/Jetson install;
- real local-model inference and offline-mode inference;
- persistence registration plus sign-out/reboot recovery;
- watchdog crash/recovery;
- sustained load, latency and thermal behavior;
- hard-offline outbound probes and OS network review;
- staged offline Python/GGUF import where applicable;
- real malware scanner availability/behavior;
- encrypted private-state export/transfer/import/restore.

Do not spend cloud or local AI effort pretending these can be VERIFIED without the target environment.

## 12. Professional tools remain external

The following remain `EXTERNAL_LICENSE` until their exact legal/licensed environment exists and a real adapter/E2E Evidence cycle is possible:

- COMSOL
- MATLAB
- APx
- KLIPPEL
- SoundCheck
- ACQUA

Names in documentation, executable detection or public API descriptions are not adapters. Hardware, calibration, exact version compatibility and raw Evidence remain mandatory where applicable.

## 13. Privacy / ingress / offline boundary

Private engineering defaults to loopback. Explicit trusted-LAN mode accepts only the bounded local-address policy. Public/cloud research is a separate channel and must not silently attach customer/project/measurement/Evidence/private files.

Application privacy policy is not an OS/firmware-wide zero-exfiltration proof. Software `mode=offline` is not an air gap. Public ingress remains validation → pinned/TLS connection → redirect revalidation → quarantine → SHA-256 → local malware scan when available → risk markers → explicit Human promotion.

## 14. Supply-chain / relocation truth

Portable package SBOM/provenance and external SHA-256 sidecar provide deterministic metadata and transfer-integrity checks. They do not establish signer identity. High-assurance release/relocation still needs a trusted signing identity/key lifecycle plus destination restore and real-machine/tool/calibration acceptance.

## 15. Current product conclusion

AERIS remains **PRE_ALPHA**. The current cloud-side kernel is materially stronger than the old audit described, but the correct conclusion is still:

```text
TESTED cloud/software baselines
≠ real-machine VERIFIED
≠ 100 domain-verified engineers
≠ production-complete acoustic company
≠ commercial release ready
```

The next local Codex cycle should consume the current Core/Implementation truth, close only target-machine/software gaps that actually require the selected machine, and preserve every Human/external/license/hardware/calibration boundary above.
