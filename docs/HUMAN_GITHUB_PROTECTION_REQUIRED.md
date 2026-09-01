# Human-required GitHub Protection — Core + Implementation

AERIS uses two repositories with deliberately different authority.

**Observed 2026-09-01:** active Rulesets exist on both default branches and direct main writes are now rejected by the PR rule. No bypass actors are configured. This is real progress, but the current effective rules still need Human review because required approvals/status checks are not yet encoded as strongly as the target policy below.

## A. Canonical Core — strongest protection

Repository: `Space653000/0_JN1_AERIS`  
Branch: `main`

Core is the read-only design authority for Codex/implementation. Repository instructions and local push guards do not replace server-side authority controls.

Current observed Ruleset properties:

```text
active: YES
default branch targeted: YES
deletion blocked: YES
non-fast-forward / force-push blocked: YES
Pull Request required: YES
bypass actors: NONE
required approving reviews: 0
CODEOWNER review required: NO
required AERIS status checks in Ruleset: not observed
```

Recommended Core policy:

- keep deletion/force-push blocked;
- keep direct main update behind PR;
- no Codex/implementation bypass;
- use Human-controlled publication;
- require CODEOWNER/Human approval **only if the account/team setup can satisfy it without creating a solo-owner deadlock**;
- periodically review GitHub Apps/tokens with write authority;
- prefer signed/verified Human publication commits/tags/releases for future high-assurance Core revisions.

Core acceptance evidence should record the exact effective Ruleset, not merely `protected=true`.

## B. Implementation repository — PR + CI protection

Repository: `Space653000/0_JN1_AERIS_Local-computer-implementation`  
Branch: `main`

Current observed Ruleset properties:

```text
active: YES
deletion blocked: YES
non-fast-forward / force-push blocked: YES
Pull Request required: YES
bypass actors: NONE
required approving reviews: 0
required AERIS Portable Company CI status checks in Ruleset: not observed
```

The desired workflow is now the normal workflow:

```text
ChatGPT / Codex
→ feature/repair branch
→ changes + tests
→ Pull Request
→ Windows + Ubuntu AERIS Portable Company CI
→ review/evidence check
→ merge to implementation main
→ main CI rerun
```

Recommended implementation-main Ruleset additions:

- require the current Windows/Ubuntu AERIS CI checks before merge;
- require branch to be up to date where practical;
- dismiss stale approvals if Human approvals are adopted;
- no AI/automation bypass;
- optionally require Human approval for privacy/security/installer/professional-tool/release changes.

Do not disable the Ruleset just to make AI writes convenient.

## C. Local Core boundary remains mandatory

Every guarded Git Core cache must verify:

```text
fetch URL = canonical Core
push URL = DISABLED://...
pre-push hook = DENY
HEAD detached
HEAD == origin/main == recorded Core SHA
working tree clean
```

Air-gap snapshot mode must verify exact file inventory + SHA-256. Snapshot hash integrity is not source authenticity unless the manifest/digest is independently trusted or signed.

## D. Defense in depth

```text
Core semantic policy
+ Core remote drift gate
+ local Core content verification
+ local push guard
+ GitHub Ruleset
+ scoped credentials
+ CI/PR gate
+ Human approval for high-impact publication
```

No single layer is called "100% immutable" by itself.

## E. Verification rule

Whenever GitHub rules are changed, read back the effective Ruleset through GitHub and, where safe, test a non-destructive forbidden direct update using an automation-equivalent credential/path. A document saying protection exists is not evidence that GitHub enforces it.
