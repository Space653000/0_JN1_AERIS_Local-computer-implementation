# P02 construction supervision handoff — NOT COMPLETE

This is a **Draft PR for supervision only**. It is not a release, acceptance of
P02 as complete, permission to merge, or a claim of 100 human-equivalent engineers.
Canonical `Space653000/0_JN1_AERIS` remains read-only and receives no push.

## Exact construction baseline

- Implementation: `Space653000/0_JN1_AERIS_Local-computer-implementation`.
- Construction commit: `0752121f632db39f0e78680932baa1ef955f039f` (`0752121`).
- Remote main observed: `32ca69baa778959d01c10a72bba1a8f0c0ac7eb5`.
- Merge base: `55ef9ee9be8eac3ba8c8de804c55a53a9ea35e15`.
- Handoff branch: `codex/handoff/p02-100-engineer-0752121`.
- Reviewed Core cache: `82f4554623b2d87185dac39a3b93194af7dd5275`.

The original 13 local construction commits are preserved. Main has one separate
commit after the merge base; it has **not** been merged or rebased into this work.
The handoff HEAD adds only this SUMMARY and SNAPSHOT on top of construction.
The PR's actual HEAD SHA is available from GitHub; it is deliberately different
from the construction SHA recorded in the snapshot. No runtime was redeployed
for this documentation-only handoff.

## What is available to inspect

Review the complete source diff, not just the summary: `aeris_runtime/engineering/`,
`company/capabilities/R001` through `R100`, `skills/`, `methods/engineering/`,
`golden/engineering/`, `knowledge/engineering/`, capability routing, workflow and
Evidence integration, Core-based UI, and permanent negative/regression tests.
`SNAPSHOT.json.changed_files` enumerates the construction diff from merge base,
including source-blob SHA-256 values. No source change has been squashed away.

Historical local observations at the construction commit:

| Item | Observed result and boundary |
|---|---|
| Role maturity | L0=0, L1=0, L2=0, scoped L3=100, L4=0; at least L2=100/100 |
| Groups | Chief Council 8, Speaker 18, Microphone 18, Product Chiefs 24, Experts 20, Ops 12 |
| Skills | 42 new factory executables; 47 total registered including 5 pre-existing |
| Methods | 42 new factory methods |
| Cases | Golden 42, Negative 42, Regression 42; fixtures are synthetic/analytical |
| Knowledge | 204 authored/provenance-bearing notes and metadata; not licensed standards full text |
| Unit tests | 213 passed on local Windows; this is not the Draft PR's CI result |
| Skill workflows | 42 actually executed to Evidence, with exact replay checks |
| Product Chief workflows | 24 actual product-specific routed workflows with sealed Evidence |
| HTTP soak | Post-fix 5,400/5,400 passed; previous soak had 1 failure, retained separately |
| Capability gaps | Empty only for the declared 100-seat free-local execution contracts; not all possible engineering capabilities |

The Windows HTTP failure was reproduced at the actual request/heartbeat/atomic
replace seam. Bounded replacement retry fixed transient sharing denial; a
permanent-denial negative test preserves failure rather than inventing success.
The original failure must not be erased by the subsequent passing soak.

## Evidence privacy and verification limits

**No `.aeris` file is uploaded.** Raw Evidence, raw user/customer data, private
measurements, SQLite/WAL/SHM, project/experiment memories, model outputs, runtime
logs, screenshots, machine state and credentials stay on the local machine.
Only reviewed authored source, synthetic Golden fixtures, and metadata are public.

`SNAPSHOT.json.local_only_evidence` lists each inventoried local artifact using an
opaque ID, SHA-256, byte count, type, category and provenance pointer. Private
filenames and file contents are not copied into the public manifest. The pointer
resolves through the **local-only** map at
`.aeris/handoff/p02-0752121/PRIVATE_EVIDENCE_MAP.json` under `C:\0_JN1_AERIS`.
The 42 Skill and 24 Product Chief records reference the corresponding inventory
IDs. Mutable file hashes are observations of stable bytes during inventory, not
an atomic multi-file SQLite backup or a cryptographic attestation of truth.

A GitHub-only reviewer can examine code, contracts, numerical fixtures and hash
metadata, but **cannot independently verify excluded artifact contents**. Ask
the local operator to resolve provenance pointers and verify hashes when needed.
Non-evidence caches/toolchains and credential stores are excluded wholesale;
credentials are not published even as an Evidence inventory.

The pre-push check covers the construction tree and all newly reachable history
blobs, including secret patterns, forbidden paths and SQLite signatures. One
literal dummy localhost credential URL in a rejection test was manually reviewed
and documented; it is not a real secret. `.env.example` has no actual keys and the
tracked acoustic CSVs are synthetic Golden fixtures. Heuristic scanning is not a
proof that arbitrary sensitive information can never exist.

## Remaining gates and supervision questions

- Human: expert review of method applicability and uncertainty; R3/R4, production,
  clinical/legal/formal release approval. Automated counterreview is not Human approval.
- Hardware: real DUT, instrument, fixture, measurement-chain calibration and L4
  validation; actual reboot/logoff or second-machine acceptance where required.
- License: real professional-tool execution and rights-cleared standards full text.
- Review the limited depth and applicability of each seat's mapped methods. A
  passing synthetic fixture does not establish comprehensive domain competence.
- Check the Draft PR's actual CI and main divergence. Local test results do not
  establish Windows/Ubuntu PR CI or post-merge main acceptance.

**Do not merge. Do not publish. Do not label P02 complete.** The purpose is to
allow ChatGPT supervision of the real construction source and its truthful limits.
