# GATE-06 RETRY R1 bounded completion contract

Scope: candidate compatibility and authority repair only. Existing checkpoint
`c1f50b1` and reconciliation `20edb9a` remain recoverable. No Core write, main
merge, runtime cutover, E acceptance, paid action or new acoustic capability.

| Item | Acceptance criterion | Current evidence/status |
| --- | --- | --- |
| Preserve history | Both reconciliation parents remain ancestors | RECONCILIATION.json; verified |
| Consumer compatibility | Frozen mirrors, mixed-pointer and authority rejection tests | COMPATIBILITY.json; final regression pending |
| Full local regression | Fresh complete suite exits 0 after final source change | In progress; earlier runs not substituted |
| Privacy boundary | Candidate index contains only public source/sanitized evidence | Initial 1,717-file scan has no prohibited paths/token signatures; staged scan pending |
| Exact candidate | Clean worktree, new commit retaining merge history | Pending full regression |
| Branch publication | Existing supervision branch normal push; PR #33 remains Draft | Pending candidate |
| Exact candidate CI | Windows and Ubuntu SUCCESS at candidate SHA | Pending push |
| Publisher | Immutable next triplet links S0003 and is verified on private Supervision remote | Pending both CI platforms |

After each criterion succeeds, preserve evidence and continue without routine
confirmation. Never mark a partial item complete. Stop before unapproved
destruction, paid action, new authority or unresolved product decisions. Ordinary
test/CI waiting is not a blocker. No review-system bootstrap or additional model
review is authorized by this bounded batch. Final Human review occurs after the
Publisher; no following Gate is started automatically.
