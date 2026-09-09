# GATE-06 RETRY R1 — candidate repair, not runtime acceptance

WHAT remains the read-only `v0.7.0-blueprint.1` release at
`64576bdbe680170fc1ea27306d1a2ab494cac733` (governance `0.7.0-governance.4`).
HOW remains this Implementation repository. PR #33 stays Draft; no main merge.

## Preserved history and atomic candidate

`c1f50b1bc9e990684377a6e0c794e2dd728e1923` is recoverable through checkpoint
`codex/checkpoint/gate06-r1-c1f50b1`. Merge
`20edb9a32d368fb254a3ed62cff450970a6ed743` preserves both the 51 construction
commits and the three main commits. See RECONCILIATION.json for conflict rationale.
No reset, force push, Core write or dropped side was used.

Core lock, role registry pin, all 100 Role Pack pointers and active config
consumers move together. Role Pack original generation SHA is retained separately;
this migration grants no role maturity. Public contract mirrors are hash-pinned
and independently byte-compared to the fixed upstream commit in CI. Traceability
is schema 1; review/autopilot are schema 3 — schemas are not blindly relabeled.
COMPATIBILITY.json separates candidate compatibility from expected runtime DRIFT.
Rollback is a new revert commit, preserving reconciliation history; no live cache
or service is switched by this candidate.

## F01/F02 repair mechanism and mandatory counterexamples

Formal PASS is resolved through `aeris_runtime/release_evidence.py`, not through
caller labels. The local operator trust store has no enrollment/minting endpoint.
HMAC-SHA256 receipts bind stable signer identity, task, scope, artifact identity,
artifact bytes, sealed bundle hash, gate, decision, issue time and expiry.
The sealed `version_tuple.json` digest is also bound into every receipt and task.
Core, Implementation, checkout and running-service identities must agree; missing
observations, old running SHAs, mismatched configuration/assets and stale runtime
observations reject authority even when the receipt signature is valid. This is
tested with synthetic observations; the actual local runtime remains DRIFT.
Both receipt and source bundle have bounded age. G4/G5 require independent stable
subject and isolated context; G5 additionally requires a provisioned Human
principal and an exact-artifact approval action. All gates are re-resolved at
summary/transition time, so deleting or altering a receipt invalidates approval.

| Required rejection | Permanent test |
| --- | --- |
| nonexistent Evidence | `test_nonexistent_evidence_rejected` |
| wrong task | `test_wrong_task_rejected` |
| wrong scope | `test_wrong_scope_rejected` |
| tampered hash | `test_tampered_hash_rejected` |
| stale Evidence | `test_stale_evidence_rejected`; `test_fresh_receipt_cannot_rejuvenate_stale_source_evidence` |
| expired Evidence | `test_expired_evidence_rejected` |
| same author renamed reviewer | `test_same_author_renamed_reviewer_rejected` |
| reviewer/implementer context collision | `test_context_collision_rejected` |
| incomplete G0–G5 release | `test_incomplete_gates_release_rejected` |
| missing Human approval artifact | `test_missing_human_approval_rejected` |
| mixed Core pointers | `test_mixed_core_versions_rejected`; `test_one_old_role_pointer_rejects_entire_candidate` |
| incompatible schema consumer | `test_incompatible_schema_blocked` |
| old runtime falsely aligned | `test_runtime_old_sha_aligned_rejected` |
| missing four-way observation | `test_missing_four_way_tuple_cannot_authorize_release` |
| signed old runtime observation | `test_signed_old_runtime_tuple_still_rejected` |

Positive signed full-release and deletion-invalidation tests exercise the same
task/gate transition code. Claim Guard now resolves task-bound independent-review
receipts too; caller `approved_evidence_refs` alone is rejected. Local numerical
workflow results use `BASELINE_PASS`, which cannot authorize formal completion.
Existing four environmental Product review dispatch omissions are repaired only
to retain their already-committed acceptance paths; no new acoustics are added.

## Assurance boundaries

This is an application authority boundary, not protection against an administrator
who can rewrite the trust store, source code or filesystem. No real Human signing
key was generated, no professional release occurred, and tests use clearly marked
deterministic dummy keys in isolated temporary directories. A signed reference
does not by itself establish the semantic correctness of arbitrary claim prose.
No unsigned binary is promoted to trusted signed status.

## Regression and publication evidence

The initial complete diagnostic run had 513 tests, 2 failures and 47 errors.
The main error was baseline workflow PASS entering the new formal authority
resolver; the two failures exposed stale global-zero-gap/docs assertions.
Replacement tests enforce the frozen bounded policy rather than erasing unrelated
NOT_IMPLEMENTED capabilities. Focused checks are supporting evidence only.

Full regression and exact candidate Windows/Ubuntu CI are required before calling
this Gate ready. CI explicitly checks out the PR head SHA, not an unrelated older
or synthetic merge checkout. Its immutable run URLs and candidate SHA belong in
the PR publication record and final Supervisor snapshot; this pre-commit document
cannot contain its own future Git SHA or future CI result.

Private logs, SQLite/WAL/SHM, screenshots, raw measurement/customer/user data,
credentials, local binaries and `.aeris` stay local. Only sanitized results and
digests may be published. No earlier test SHA is substituted for candidate CI.

## Runtime and Supervisor

Observed running Implementation is `b7901fe7ca4c8bad295d52fed6ef3c12a50cd95d`,
running Core `82f4554623b2d87185dac39a3b93194af7dd5275`. Candidate publication
does not update them. `/health` remained SERVING with `company_complete=false`.
Four-way alignment is not claimed. Installer/Autopilot/sync entrypoints reject
local mutation during this Gate; hosted disposable CI is a limited test exception.

The Human-confirmed S0002 → S0003 chain and existing local Publisher remain
unchanged. `supervision_chain.py` preserves earlier helper/test work but does not
replace that Publisher. Only after both exact-candidate CI platforms succeed,
run the existing Publisher and verify the next immutable snapshot links to S0003
in `Space653000/0_JN1_AERIS_Supervision`. No merge, runtime cutover or E acceptance.
