# P5 — Engineer Factory (concrete acceptance criteria)

Unlike P1-P4, this phase already has a rich, pre-existing 487-line spec:
`docs/AERIS_PROFESSIONAL_COMPANY_BUILD_100_ENGINEER_CAPABILITY_FACTORY.md`
("100-Engineer Capability Factory"). P5.1-P5.9 map onto that document's
sections rather than being invented fresh. Its own stated primary stop
condition (section 13): `100_role_L2 = 100/100`, and the live API's
`ROLE_CAN_BE_MADE_L2_WITH_FREE_LOCAL_SOFTWARE` field is currently `true`,
meaning the system's own self-assessment says more roles can still reach L2
with free local software -- so this is legitimate, in-scope, expected work,
not scope creep.

## Where P3 left off

P3 ("Golden Engineer") got the execute -> evidence -> accept pipeline
actually running: 73/100 roles reached L2. The remaining 27 have no
role-specific domain execution contract implemented yet:

- **Chief Council (7):** R001-R004, R006-R008 -- governance/architecture
  oversight roles. A bounded, deterministic "execution contract" is a poor
  fit for what these roles actually do (cross-cutting judgment, not a
  single measurable analysis); may legitimately stay non-L2 by nature
  rather than by gap.
- **Product Chiefs (7):** R062-R068 (VR/XR, automotive, AMR, quadruped,
  humanoid, conference device, directional mic array) -- structurally
  similar to the 24 existing product-chief domain contracts
  (`tests/test_capability_factory.py`'s
  `test_twenty_four_product_packs_have_distinct_architecture_and_executable_plans`);
  plausible to extend using the same bounded-analytical pattern.
- **Distinguished Experts (7):** R078, R083-R088 (DOE/statistics, codec/
  network, ML, data engineering, competitive benchmark, patent research,
  frontier research) -- mixed: DOE/statistics and data engineering could
  plausibly get a bounded numeric contract; competitive benchmark and
  patent research are desk-research roles where a deterministic "execution"
  contract may not be the right model at all.
- **Engineering Ops (6):** R091-R093, R095-R096, R100 (test automation, lab
  instrument control, factory EOL/QC, supplier quality, reliability/HALT,
  autonomous optimization) -- process/operations roles; some (reliability/
  HALT has real textbook formulas, e.g. Arrhenius acceleration) could get a
  bounded analytical contract.

## P5.1 — Materialize domain contracts for roles where it's a good fit
**Requires:** new role-specific execution contracts (method + golden fixture
+ review-policy binding, same shape as the 73 existing ones), built with the
same conservative, bounded-scope, explicit-exclusions style already used
(see e.g. `methods/roles/thermal-rc.json`'s literal textbook RC time-constant
formula) -- not fabricated thresholds.
**Status: investigated, not yet built this tick.** Authoring new acoustic/
domain contracts requires getting the underlying engineering right (unlike
P3, which only had to *run* already-reviewed contracts). Doing this well
needs picking one concrete, textbook-formula-backed case at a time and
verifying it against a real reference calculation, not batching many roles
at once under time pressure. Next tick's target: one Product Chief role
(most structurally similar to existing patterns) as a proof case.

## P5.2 — Honest boundary: some roles may never need a domain contract
**Requires:** roles that are inherently judgment/oversight/desk-research
roles (Chief Council, competitive benchmark, patent research) are not forced
into a fake "bounded execution" just to move a percentage. The maturity
rubric's L1 ("complete referenced contract") may be the honest ceiling for
some of these without a real physical/analytical capability behind it.
**Status: this document's own accounting above.**

## P5.3 — Free Tool Bus adapter software baseline (re-checked, already correct)
**Requires:** per section 9 of the parent spec, COMSOL/MATLAB/Ansys/APx/
KLIPPEL/SoundCheck/ACQUA stay `EXTERNAL_LICENSE`/`BLOCKED_EXTERNAL` until a
real license exists, with the free-local-baseline substitute explicitly
tested and never claimed equivalent to the paid tool.
**Status: already correct -- an earlier draft of this document wrongly
called `completion.py`'s `comsol_adapter`/`matlab_adapter`/etc. GATE_CHECKS
"a placeholder pointing at the wrong thing." Re-checked against
`config/maturity.json`: each of these 6 gates' `gate_software_baselines`
entry explicitly declares its tested claim as "FREE_LOCAL_BASELINE ...;
[tool] equivalence is not claimed," and `_free_acoustics()` (the function
all 6 GATE_CHECKS point to) verifies exactly that -- the free baseline runs
and professional-tool equivalence is denied. That is the correct, honest
check for what's actually claimed. No change needed here; this entry stays
only as a record that the claim was checked and confirmed correct, not to
repeat a mistaken "gap" finding.

## P5.4 — Expand the Golden Acoustic Factory (section 10)
**Requires:** broader golden suites (Speaker/Microphone/Array/DSP/Product/
Failure), each case carrying input/expected/tolerance/units/method version/
reason/negative variant/failure expectation/SHA-256.
**Status: partially satisfied.** `golden/acoustics/v1/` and 73 roles'
`golden/roles/R*/` already follow this shape; broadening coverage further is
real but large content work like P4.4, not a single-tick item.

## P5.5 — Capability-driven Dynamic Pod Router (section 11)
**Requires:** pod routing uses product/transducer/lifecycle/requirement/
risk/evidence/skills/tools/maturity, not keyword matching, and outputs
lead/executors/reviewer/evidence-curator with a reason per selection.
**Status: verified done.** `aeris_runtime/engineering/orchestration.py`'s
`route_pod()` explicitly rejects keyword-only routing ("explicit known
needed_skills required; keyword-only routing is not supported"), requires
product/transducer/lifecycle/risk/requirement/required_evidence/
available_tools, and its output carries `lead`, `executors`, `reviewer`,
`evidence_curator`, and a `selection_reason` per selected role. Matches the
spec as written.

## P5.6 — Dashboard as company capability map (section 12)
**Requires:** the dashboard should let a human see real coverage (which
roles, which skills, which gaps) at a glance.
**Status: substantially satisfied by P1.4's capability graph + P4's Skills
Library**, built before this phase was named. Re-verify against section 12's
exact wording next tick rather than assuming full overlap.

## P5.7 — Reviewer allocation actually challenges results (Core engineering criterion)
**Requires:** the full loop in the parent spec's final section: requirement
-> specialist selection -> method -> free local analysis -> Evidence ->
verify -> **independent Reviewer challenges the result** -> correct/refine
-> report -> reproducible Knowledge. The "independent Reviewer challenges"
step is the same mechanism P3.6 found is not yet real (no code path sets
`role_l3_accepted` True).
**Status: same open item as P3.6** -- needs the Human's definition of what a
qualified challenge/review requires before building it.

## P5.8 — Total-count accounting (section 13's "final report" requirement)
**Requires:** total roles, L0-L4 counts, total executable skills/methods/
golden/negative/regression cases, per-group coverage, unresolved gaps --
all as a real, re-derivable report, not prose.
**Status: mostly available live** via `GET /api/v1/capabilities` already;
wiring a dedicated `progress_verify` check for this is a natural, low-risk
next increment (same pattern as P3.2/P3.3).

## P5.9 — Do not stop at green tests
**Requires:** treating `100_role_L2 = 100/100` as the real bar, not "tests
pass" or "percentage looks good."
**Status: acknowledged and tracked** -- 73/100 is the honest current number,
not rounded up, and this document says so plainly.

## Sequencing
Lowest-risk, highest-confidence next steps: P5.3 (adapter interface stubs,
purely declarative) and P5.8 (a progress_verify check for the existing
live coverage numbers). P5.1 (new domain contracts) is real and valuable
but needs one careful, verified case at a time, not a batch. P5.5/P5.6 need
a verification pass before claiming status either way. P5.7 is blocked on
the same Human decision as P3.6.
