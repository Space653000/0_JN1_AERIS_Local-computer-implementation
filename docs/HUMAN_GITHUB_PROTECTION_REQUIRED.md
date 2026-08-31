# Human-required GitHub Protection — Canonical Core

Canonical Core: `Space653000/0_JN1_AERIS`.

## Why this remains Human-required

Repository files can tell Codex "do not write", and local cached clones can disable their push URL/hook. Those controls do **not** remove server-side write permission from a GitHub credential that already has `push/admin` authority.

The current ChatGPT GitHub integration exposes read access to branch/ruleset state but does not expose a mutation for repository rulesets/branch protection. Therefore AERIS must not pretend this was completed automatically.

## Required GitHub-side outcome

For `0_JN1_AERIS/main`, configure a GitHub ruleset or branch protection so normal automation/Codex credentials cannot directly modify canonical `main`.

Recommended policy:

- target branch: `main`;
- restrict direct updates/deletions/force-push;
- require Human-controlled review/approval for publication path;
- require CODEOWNER approval where supported;
- do not give Codex/local implementation credentials bypass rights;
- keep the implementation repo separate and writable;
- periodically review installed GitHub Apps/tokens with write permission.

The exact GitHub UI/options depend on account/repository plan and current GitHub product behavior. Verify the effective rule in the repository's Rules/Branches settings after saving.

## Acceptance evidence

Do not mark `Core server-side protection = VERIFIED` until a Human records at minimum:

```text
repository: Space653000/0_JN1_AERIS
branch: main
protection/ruleset: ENABLED
force push: DENIED
unauthorized direct update: DENIED
Codex/implementation credential bypass: NO
verified_at:
verified_by:
```

A stronger test is to use a non-owner test credential representing the automation role and confirm that a direct push/update is rejected. Do **not** test destructive operations against production `main` with an owner credential.

## Local boundary remains required too

Even after GitHub-side protection, local Core caches must retain:

```text
origin push URL = DISABLED://...
pre-push hook = DENY
checkout = detached origin/main
```

Defense in depth is intentional: GitHub permission + local Git guard + agent policy.
