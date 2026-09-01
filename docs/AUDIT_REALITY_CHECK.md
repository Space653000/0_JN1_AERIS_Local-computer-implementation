# AERIS Reality Check / Anti-Fantasy Audit

**Status date:** 2026-09-01  
**Applies to:** `Space653000/0_JN1_AERIS_Local-computer-implementation`  
**Canonical design authority:** read-only `Space653000/0_JN1_AERIS@main`

## 1. Non-negotiable truth rule

AERIS uses:

```text
NOT_IMPLEMENTED → IMPLEMENTED → TESTED → VERIFIED
```

External dependencies that cannot be completed in this repository use `BLOCKED_EXTERNAL`.

No AI, README, dashboard, installer or Human optimism may promote a capability by prose alone.

- `IMPLEMENTED` = code/config exists.
- `TESTED` = automated tests exercise the claimed contract and pass.
- `VERIFIED` = required real-machine / real-tool / real-evidence acceptance passes for a specified configuration.
- CI green means only the checks executed by that CI run passed.
- A 100-seat registry means 100 capability slots exist; it does **not** mean 100 mature acoustic engineers already exist.

Machine-readable source: `config/maturity.json`.

## 2. Current product stage

**PRE_ALPHA Portable Company Kernel.**

Existing real baseline includes:

- 100-seat registry count/grouping;
- local/private chat routing to Ollama-compatible local AI;
- explicit public-research-only cloud channel;
- application-level cloud-egress policy and DLP screening;
- local SQLite Knowledge baseline;
- Windows/Linux CI kernel baseline;
- Machine Profile detection baseline;
- one-click installer kernel;
- read-only cached Core sync/drift mechanism;
- portable software packaging;
- real-machine local/offline acceptance scripts;
- encrypted private-state export/import mechanism using `age`.

The reliability-hardening branch adds, pending PR CI and subsequent merge:

- fail-closed online/offline installer behavior;
- staged Windows Python + staged GGUF model verification/import;
- explicit unsupported-machine behavior;
- self-cleaning Knowledge index and FTS5 fallback;
- Core air-gap snapshot with exact file hashes;
- pinned public-IP TLS ingress to reduce DNS-rebinding TOCTOU;
- quarantine, malware scanner integration, prompt-injection/content-risk flags and Human promotion;
- private-state tar rejection of links/devices/FIFO/traversal;
- multi-path HardOffline probes with non-absolute claim wording;
- cloud secret-file support;
- pinned GitHub Actions commits;
- SPDX 2.3 file inventory + provenance + SHA256SUMS in Software Images;
- Human–AI Reliability Contract and Local Verification SOP.

These branch changes are **not promoted to TESTED merely because they are written**. Their state remains conservative until CI/real-machine evidence exists.

## 3. Still not a completed professional acoustic company

The following remain materially incomplete:

- 100 executable Role Contracts;
- mature acoustic Skill library;
- deterministic Methods library;
- live standards registry with lifecycle refresh;
- Dynamic Pod engine;
- workflow execution/state engine;
- Evidence Bundle engine and append-only audit;
- G0–G5 verification engine;
- Golden acoustic datasets/regression suite;
- professional acoustic corpus / semantic/provenance retrieval;
- COMSOL/MATLAB/APx/KLIPPEL/SoundCheck/ACQUA production adapters;
- live local Dashboard/Workspace/Services backend;
- OS-level DLP/network/process enforcement;
- clean-machine Windows/Linux/Jetson verification evidence;
- full-company relocation verified on a second machine;
- production release signing/attestation and complete commercial/legal release gate.

## 4. Core repository write boundary

The Core repo is defined read-only for Codex/implementation in its own governance files.

Local Core representations are either:

- guarded Git cache: disabled push URL + deny pre-push hook; or
- checksum-manifested snapshot: no Git remote, canonical Core SHA + exact per-file hashes.

GitHub server-side protection is a separate Human-controlled layer. A live Ruleset now exists and direct implementation-to-main writing has been observed blocked by GitHub; the Human should still review the exact Ruleset requirements (approvals/status checks/code-owner/bypass policy) rather than equating “a ruleset exists” with maximum protection.

Implementation changes now follow branch → CI → PR → main instead of normal direct-to-main mutation.

## 5. Privacy claim boundary

AERIS can truthfully claim:

> AERIS application code does not automatically attach local Memory, Evidence, files or customer data to cloud research requests; private engineering chat is hard-routed to local AI.

AERIS must **not** claim:

> No process on the computer can ever leak data.

That stronger statement cannot be proven by a Python router. It requires OS/network/process controls and, for highest sensitivity, separate security zones or air gap.

`research` is a public channel. Best-effort DLP cannot prove absence of private information; the Human still classifies the query.

## 6. Public ingress claim boundary

Public URL ingress is untrusted input.

Hardening target:

```text
public-only DNS answers
→ connect to validated IP
→ TLS hostname validation
→ revalidate redirects
→ quarantine
→ hash
→ local malware scanner if present
→ content/prompt-injection markers
→ Human promotion
```

This reduces SSRF/rebinding and content-risk exposure but does not prove an internet artifact is factually correct, legally reusable, or malware-free when no trusted scanner/signature exists.

Downloads are never automatically treated as Knowledge authority.

## 7. Offline claim boundary

`mode=offline` blocks AERIS cloud routing and public URL ingress. It is not an air gap by itself.

A machine is not hard-offline accepted until:

1. all required local runtime/model/data/Skills/tools are already present;
2. real local inference succeeds;
3. real offline-mode inference succeeds;
4. external network is physically disconnected or intentionally blocked;
5. multi-path outbound probes do not succeed;
6. acceptance evidence is preserved.

Even then, the correct evidence statement is “tested outbound paths were blocked”, not mathematical proof about every possible process/protocol/firmware path.

## 8. Model baseline

Default continuity baseline is `qwen3:4b-instruct` through Ollama-compatible API.

A local model is replaceable compute. It is not AERIS identity and not evidence of 100-person professional capability. Exact model/tag/digest/license must be reviewed for the actual commercial/formal release.

## 9. Professional tools

COMSOL, MATLAB, APx, KLIPPEL, SoundCheck, ACQUA, Ansys and Simcenter are external/licensed dependencies.

Documentation or detection does not equal an adapter. Promotion to VERIFIED requires legal install, exact version capture, implemented adapter, tool-specific E2E and where applicable hardware/calibration/raw evidence.

## 10. Relocation truth

There are distinct artifacts:

1. **Software Company Image** — public software only; no secret/private state.
2. **Release metadata** — SBOM, provenance and checksums for the software inventory.
3. **Encrypted Private State** — local state encrypted with `age`.
4. **Private Asset Pack** — model weights, proprietary installers/licenses, drivers/calibration/private datasets/credentials.
5. **Destination acceptance evidence** — proves what actually works after restore.

A Software ZIP/tarball alone is never called a full-company relocation.

## 11. Supported-machine truth

AERIS does not claim “any computer”.

The valid statement is:

> A machine is a supported baseline only if a versioned AERIS Machine Profile exists; it is VERIFIED only after that physical machine passes required acceptance.

No profile → `UNSUPPORTED_PROFILE`, not guessed compatibility.

## 12. Release rule

No release may be called `COMPLETE`, `PRODUCTION READY`, `100 ENGINEERS READY`, `OFFLINE VERIFIED`, `PRIVACY GUARANTEED`, `ALL AI PROVIDERS SUPPORTED`, `ALL COMPUTERS SUPPORTED`, or `FULL COMPANY RELOCATABLE` unless the exact scoped capability is VERIFIED and the required evidence exists.

AERIS treats a gate that finds a real defect as a successful reliability mechanism.
