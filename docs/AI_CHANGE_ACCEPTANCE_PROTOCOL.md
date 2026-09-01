# AERIS AI Change Acceptance Protocol

This protocol exists so AERIS quality does not depend on an AI remembering every previous mistake.

## Mandatory closure sequence

For every software defect, regression, contract drift or deployment blocker:

```text
READ CURRENT REMOTE MAIN
→ REPRODUCE THE EXACT FAILURE
→ WRITE A REGRESSION TEST/GATE
→ IMPLEMENT THE FIX
→ RUN AFFECTED TESTS
→ RUN FULL WINDOWS + UBUNTU PR CI
→ MERGE ONLY WHEN ALL REQUIRED JOBS PASS
→ RUN/VERIFY POST-MERGE MAIN CI
→ ONLY THEN PERFORM ONE NECESSARY REAL-MACHINE ACCEPTANCE CYCLE
```

PR CI success alone is not closure. A fix is GitHub-closed only after the merged `main` commit passes its own required CI.

## Local-token conservation

A local machine is not the default software debugger. Any defect reproducible in GitHub CI must be converted into a permanent regression gate and fixed in GitHub first. Local Codex is reserved for machine-specific facts such as actual installed runtimes, drivers, GPU, Ollama inference, reboot/persistence, offline networking, proprietary licenses, instruments and calibration.

When a local machine discovers a software bug:

```text
local evidence
→ exact minimal reproduction
→ GitHub regression gate
→ GitHub repair PR
→ Windows + Ubuntu CI
→ merge
→ post-merge main CI
→ one local rerun
```

Do not repeatedly spend local Token rediscovering the same cloud-reproducible defect.

## Regression tests are permanent evidence

A defect is not considered repaired merely because code changed. The repair must include a deterministic regression test or CI gate that fails for the defective behavior and passes for the corrected behavior whenever that is technically possible.

A regression gate must not be silently removed or weakened. If a gate becomes obsolete, replacement coverage and the reason for replacement must be explicit in the same PR.

For Windows deployment, the following are quality-critical permanent gates:

- every tracked `.ps1` file parses with the PowerShell parser;
- Windows Store/App Execution Alias `python.exe` must not be accepted unless it actually executes a supported Python;
- `py -3.11`, then supported `py -3`, must be tried before generic `python`;
- the official Windows one-click installer smoke must pass;
- the Windows Full Autopilot entrypoint smoke must pass.

## Cross-file truth changes are atomic

When canonical Core changes, the Implementation may deliberately accept it only after semantic review. The following tracked values must move together in one repair/change set:

```text
core.lock.json                         baseline_sha
config/core_alignment.json             canonical_core.reviewed_sha
config/autopilot.json                  canonical_core_sha
company/company.manifest.json          core_target.reviewed_sha
config/maturity.json                   evidence_snapshot.canonical_core_reviewed_sha
```

Any mismatch is a hard failure, not a warning.

## Authority-document consistency

Higher-authority documents must not contradict each other. Core governance CI must fail if `AGENTS.md`, `aeris.autopilot.json`, `aeris.policy.yaml` and the Full-Build SOP disagree on the trigger, target-path resolution, default AI roles, scheduling, Human Gates or software-gap closure.

## No-false-done rule

Use these meanings strictly:

```text
IMPLEMENTED = code/config exists
TESTED      = stated automated test scope passed
VERIFIED    = required real-machine/tool/physical evidence also passed
BLOCKED_EXTERNAL = blocked by a real license/hardware/credential/calibration/external dependency
```

Dashboard reachability, a healthy process, passing CI or an AI assertion never upgrades a capability beyond its evidence.

## Human Gate rule

Do not return routine engineering or installation choices to the Human. Stop only for a genuine Human/external gate: unsafe/ambiguous target, denied OS privilege, License/EULA, secret/hardware token, physical fixture/instrument/calibration, destructive unrelated system action, one-time reboot/logoff evidence, Core policy publication, or R3/R4 formal/customer/production release.

## Required AI completion report

Before saying a GitHub repair is complete, the AI must be able to state, from current evidence:

```text
exact Core main SHA
exact Implementation main SHA
regression test/gate added
PR CI Windows result
PR CI Ubuntu result
post-merge main CI Windows result
post-merge main CI Ubuntu result
remaining items requiring real-machine evidence
remaining genuine external/Human blockers
```

If any field is unknown, the AI must say the GitHub repair is not yet closed.
