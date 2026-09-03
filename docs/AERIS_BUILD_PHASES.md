# AERIS Build Phases — Persistent Cross-Machine Execution Memory

This file is the durable continuation contract for AERIS construction.

The Human should be able to open/select one safe local workspace and provide only:

```text
https://github.com/Space653000/0_JN1_AERIS
https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation
```

Codex must then read this catalog plus `config/build_phases.v1.json`, inspect real local evidence, and **resume from the first unsatisfied phase instead of repeating previously completed work**.

## Permanent rule for future AERIS expansion

Every major new construction prompt/spec must be persisted in this Implementation repository as a versioned build-phase document and added to the machine-readable phase catalog.

A chat prompt is temporary. A build-phase spec in GitHub is durable organizational memory.

Future phase additions must preserve:

- Canonical Core remains read-only WHAT/SSOT.
- Implementation remains executable HOW.
- zero-cost/no-Claude default path.
- evidence-based completion detection.
- no phase is considered complete from prose alone.
- completed phases are not rerun unless their completion evidence is missing, stale, invalid, incompatible with current Core, or explicitly invalidated by a later phase.
- later phases may strengthen earlier phases but must not silently weaken truth, evidence, safety or regression gates.

## Phase sequence

### Phase 01 — Local Software Completion Pass

Spec: [`AERIS_LOCAL_SOFTWARE_COMPLETION_PASS.md`](AERIS_LOCAL_SOFTWARE_COMPLETION_PASS.md)

Purpose:

- converge Core UI into the real local UI;
- close every safe zero-cost software-local gap;
- distinguish software gaps from genuine Human/External gates;
- prove local platform acceptance.

Primary stop condition:

```text
SOFTWARE_LOCAL_FIXABLE = 0
```

Expected evidence includes `.aeris/state/SOFTWARE_COMPLETION.json` and local acceptance/autopilot evidence.

### Phase 02 — Professional Company Build / 100-Engineer Capability Factory

Spec: [`AERIS_PROFESSIONAL_COMPANY_BUILD_100_ENGINEER_CAPABILITY_FACTORY.md`](AERIS_PROFESSIONAL_COMPANY_BUILD_100_ENGINEER_CAPABILITY_FACTORY.md)

Purpose:

- stop treating installer/dashboard as the main product;
- materialize all 100 acoustic capability seats;
- build executable Skills, Methods, Knowledge, Golden cases, evaluations and free local toolchain;
- build Kairos-style organizational memory/harness while preserving `Memory != Evidence`.

Primary stop condition:

```text
100_role_L2 = 100 / 100
```

and every L2 role has a real executable local capability path, not merely a persona/prompt.

## Resume algorithm

On any supported machine:

1. Read Core governance and verify Core read-only integrity.
2. Read this file and `config/build_phases.v1.json`.
3. Inspect local state/evidence rather than assuming prior completion.
4. For each phase in ascending order:
   - if completion contract is valid and evidence is current, mark `SATISFIED` and do not repeat its full build;
   - if evidence is partial/stale/invalid, run only the necessary repair/acceptance scope;
   - if unsatisfied and no Human/External gate blocks it, execute the phase automatically;
   - preserve genuine Human/External gates without manufacturing completion.
5. Continue into later phases automatically when earlier phase contracts are satisfied.
6. Report the exact current phase and next unresolved capability gap.

## Future phases

When the Human and ChatGPT define Phase 03, Phase 04, etc.:

1. add `docs/AERIS_<PHASE_NAME>.md`;
2. append it here;
3. append a machine-readable entry to `config/build_phases.v1.json`;
4. update `AGENTS.md` read/resume contract if execution semantics change;
5. add deterministic validation for the new phase contract when feasible;
6. merge through normal Implementation PR/CI governance.

This is how AERIS avoids rebuilding organizational knowledge from chat history on every new computer.
