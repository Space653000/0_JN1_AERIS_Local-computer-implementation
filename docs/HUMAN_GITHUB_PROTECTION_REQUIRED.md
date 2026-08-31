# Human-required GitHub Protection — Core + Implementation

AERIS uses two repositories with deliberately different authority.

## A. Canonical Core — strongest protection

Repository: `Space653000/0_JN1_AERIS`  
Branch: `main`

Repository files can tell Codex "do not write", and local cached clones can disable their push URL/hook. Those controls do **not** remove server-side write permission from a GitHub credential that already has `push/admin` authority.

The current ChatGPT GitHub integration exposes read access to branch/ruleset state but does not expose a mutation for repository rulesets/branch protection. Therefore AERIS must not pretend this was completed automatically.

### Required Core outcome

Configure a GitHub ruleset or branch protection so normal automation/Codex credentials cannot directly modify canonical `main`.

Recommended policy:

- target branch: `main`;
- block force-push and deletion;
- restrict direct updates;
- require Human-controlled publication/review path;
- require CODEOWNER approval where supported;
- do not give Codex/local-implementation credentials bypass rights;
- periodically review GitHub Apps/tokens with write permission.

Acceptance evidence:

```text
repository: Space653000/0_JN1_AERIS
branch: main
protection/ruleset: ENABLED
force push: DENIED
deletion: DENIED
unauthorized direct update: DENIED
Codex/implementation credential bypass: NO
verified_at:
verified_by:
```

A strong test uses a non-owner test credential representing the automation role and confirms a direct update is rejected. Do **not** test destructive operations against production `main` with an owner credential.

## B. Implementation repository — PR + CI protection

Repository: `Space653000/0_JN1_AERIS_Local-computer-implementation`  
Branch: `main`

This repository is writable construction space, but long-term reliability is stronger if `main` stops accepting unreviewed direct changes.

Recommended target workflow after the ruleset is enabled:

```text
ChatGPT / Codex
→ feature branch
→ changes + tests
→ Pull Request
→ AERIS Portable Company CI required PASS
→ review / evidence check
→ merge to implementation main
```

Recommended implementation-main rules:

- block force-push/deletion;
- require Pull Request before merge;
- require current `AERIS Portable Company CI` status check to pass;
- require branch to be up to date before merge where practical;
- dismiss stale approvals after new commits where practical;
- do not allow automation to bypass required checks;
- optionally require Human approval for security/privacy/installer/tool-adapter changes.

This does **not** make the implementation repo read-only. It changes the write path from "direct main mutation" to "branch → CI → PR → merge".

Acceptance evidence:

```text
repository: Space653000/0_JN1_AERIS_Local-computer-implementation
branch: main
protection/ruleset: ENABLED
force push: DENIED
deletion: DENIED
PR required: YES
AERIS Portable Company CI required: YES
bypass for normal AI automation: NO
verified_at:
verified_by:
```

## C. Local Core boundary remains required

Even after GitHub-side protection, every cached Core clone must retain:

```text
origin push URL = DISABLED://...
pre-push hook = DENY
checkout = detached origin/main
```

Defense in depth is intentional:

```text
Agent policy
+ local Git guard
+ GitHub server ruleset
+ scoped credentials
+ CI/PR gate
```

## D. Important transition note

Until the implementation-main ruleset is enabled, ChatGPT may still be able to write directly to implementation `main`. Once the Human enables PR-required protection, future AERIS development should switch to feature branches and Pull Requests rather than weakening the ruleset for convenience.

The exact GitHub UI/options depend on repository/account plan and current GitHub product behavior. Verify the effective rule after saving; never infer protection merely from the existence of this document.
