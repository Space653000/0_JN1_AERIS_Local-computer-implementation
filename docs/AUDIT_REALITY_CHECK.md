# AERIS Reality Check / Anti-Fantasy Audit

**Status date:** 2026-09-01 (Asia/Taipei)  
**Applies to:** `Space653000/0_JN1_AERIS_Local-computer-implementation`  
**Canonical design authority:** read-only `Space653000/0_JN1_AERIS@main`  
**Reviewed Core SHA:** `bde158944ac21f076f39894600e172136c3a8c5a`

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

## 2. Fourth-audit center-philosophy result

Overall direction remains aligned with canonical Core:

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

However the audit found real implementation drift/holes and did not accept them as harmless:

1. implementation Constitution had weakened the Core mic-algorithm axes from `noise/distance/azimuth/speaker/language` to a vague `scenario` form;
2. guarded Git Core-cache verification checked write guards but did not prove local cached content/HEAD matched the recorded Core SHA;
3. private engineering was routed through the `local` adapter but the configured local base URL itself was not constrained against a public endpoint;
4. Linux/Jetson offline logic could treat a staged `ollama-install.sh` bootstrap script as if it were an air-gap runtime installer;
5. maturity/audit text still referred to a hardening PR as pending after that PR and main CI had already passed;
6. generic doctor `READY` wording could be misread as whole-company readiness;
7. package metadata had internal checksums but no external archive digest;
8. implementation had preserved only a 5–15 pod target instead of Core's ordinary 2–8 / complex 5–15 distinction.

These are repairable engineering defects, not impossible architecture. The current repair branch addresses them and remains `IMPLEMENTED` until Windows+Ubuntu CI passes.

## 3. Current verified/tested kernel baseline before current repair promotion

Main commit `16e0b85f5cb68926d44d2a77c75b3c5eba0a42bb` passed GitHub Actions main run 74 on Windows and Ubuntu for its automated scope, including:

- compile/unit/security tests;
- 100-seat manifest validation;
- Core remote drift gate;
- Knowledge rebuild;
- machine profile detection;
- mode switching;
- scoped doctor behavior available at that revision;
- installer smoke with external runtime intentionally skipped;
- SPDX/provenance generation;
- Windows/Linux portable package smoke.

This does **not** prove clean-machine installation, real hardware, real professional tools, offline network isolation or Company Done.

## 4. Core P0 priority gap — the main strategic risk now

Canonical Core explicitly prioritizes trust infrastructure before a mature autonomous organization.

The implementation currently has substantial deployment/privacy/portability work, but the following central AERIS P0/P1 capabilities remain materially absent:

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

Therefore the next major development priority must pivot from mostly deployment hardening to the Core P0 engineering-trust foundation. Otherwise AERIS could become a well-protected portable AI shell rather than the intended Acoustic Engineering Organization OS.

## 5. Core repository boundary

Canonical Core is never written by implementation/Codex.

Current tracked `core.lock.json` matches reviewed Core main SHA. Remote drift CI is read-only and fails if Core changes.

Local Core representations:

- guarded Git cache; or
- checksum-manifested air-gap snapshot.

The repaired Git-cache verification requires canonical fetch URL, disabled push URL, deny hook, detached HEAD, clean working tree and equality of `HEAD == origin/main == recorded Core SHA`.

Snapshot exact-file hashes provide integrity relative to the trusted manifest. They do **not** prove source authenticity if an attacker can replace both snapshot and manifest. High-assurance release/relocation still needs signed/trusted manifest or package attestation.

## 6. GitHub server-side governance

Active Rulesets now exist on both repositories and direct main writes are blocked by the PR rule. No bypass actor is configured.

Current Ruleset limitation observed during this audit:

- required approving review count = 0;
- no CODEOWNERS review requirement;
- no required CI status check is encoded in the Ruleset itself.

Therefore the Human should finish the chosen governance policy. For the implementation repo, required Windows/Ubuntu AERIS CI checks are strongly recommended. For a solo-owned Core, review-count policy must be chosen so it does not create an impossible self-deadlock while still preventing AI bypass.

## 7. Privacy boundary

AERIS may truthfully claim only the scoped application behavior it actually enforces.

Private engineering endpoint policy after repair:

```text
loopback (default)
OR
explicit trusted_lan + literal RFC1918/ULA/loopback IP
```

A global/public IP or arbitrary hostname is rejected as a private local provider. Cloud/public research remains a separate explicit channel with no automatic Memory/Evidence/customer-file attachment.

This still cannot prove that unrelated software, compromised OS/firmware or an authorized Human cannot exfiltrate data. Strong deployments require firewall/process/filesystem isolation or air gap.

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

This reduces SSRF/rebinding/content-risk exposure. It does not prove downloaded information is true, legally reusable or malware-free. Approved public ingress is not automatically canonical Knowledge.

## 9. Offline truth

Software `mode=offline` is not an air gap.

A clean Linux/Jetson machine with no Ollama cannot be made genuinely offline merely by staging `ollama-install.sh`, because that script is a bootstrap installer and can require network downloads. Repaired behavior blocks this case instead of pretending success.

A machine/workflow is not `OFFLINE VERIFIED` until local dependencies exist, Core verifies, real local/offline inference passes and applicable Hard Offline/network evidence is retained.

## 10. Supported-machine truth

A versioned profile match is only a profile match. It is not equivalent to full resource qualification or real-machine verification.

`machine_resource_qualification` remains unfinished: profile-specific OS/version/RAM/free-disk/accelerator/latency/headroom acceptance still needs to become a formal gate.

## 11. Knowledge truth

Current SQLite/FTS baseline is a self-cleaning local text index. It is not the final AERIS professional acoustic Knowledge System.

Canonical knowledge must eventually follow:

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

COMSOL, MATLAB, APx, KLIPPEL, SoundCheck, ACQUA, Ansys and Simcenter remain external/licensed dependencies. A README, detected executable or public API documentation is not an adapter.

`VERIFIED` requires the exact installed/versioned environment, implemented adapter, E2E execution and applicable hardware/calibration/raw evidence.

## 13. Core internal consistency note for Human review

Canonical Core itself contains one policy area that should eventually be consolidated by Human-controlled publication:

- the Master Baseline risk section describes R0–R3;
- the later Web UI / Control Plane baseline defines R0–R4, with R4 for customer/official release.

Implementation follows the later R0–R4 control-plane model because it is more explicit for formal release. This is not permission for implementation to rewrite Core; the Core should eventually expose one canonical machine-readable Risk Policy.

## 14. Relocation / supply-chain truth

A complete move is not one ZIP.

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

External `.sha256` proves transfer integrity against the sidecar. It is not signer identity. Release signing/attestation remains NOT_IMPLEMENTED.

## 15. Still not a completed professional acoustic company

The implementation remains **PRE_ALPHA**. It is not legitimate to claim:

- `100 ENGINEERS READY`;
- complete Skills/Methods/Standards;
- production Dynamic Pod;
- complete Evidence/G0–G5;
- verified professional tool adapters;
- absolute OS-wide zero egress;
- all computers/all AI providers supported;
- clean-machine Windows/Linux/Jetson verified;
- full-company relocation verified;
- production/commercial release ready;
- guaranteed revenue/profit.

## 16. Final fourth-audit conclusion

No examined AERIS north-star requirement requires fictional physics or a nonexistent category of software. The architecture is engineering-feasible **as a staged system with explicit supported configurations and external dependencies**.

But this is not equivalent to saying every target is already implemented, or that arbitrary hardware/provider/tool/data can be guaranteed 100% compatible.

The valid 100% statement is narrower:

> For one explicitly specified AERIS configuration and workflow, every required gate can eventually be required to produce evidence and pass before that scope is called VERIFIED.

That is the standard this repository must enforce.
