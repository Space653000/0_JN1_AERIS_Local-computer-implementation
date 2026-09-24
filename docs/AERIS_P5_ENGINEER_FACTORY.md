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
**Status: done.** A later session built exactly this, one role at a time,
each hand-verified against exact closed-form math before being written into
its golden fixture: R096 (HALT binomial), R093 (Cpk/gage R&R), R092
(instrument-sequence safety), R095 (incoming-lot sampling), R100 (next-
experiment safety), R091 (test-automation retry/pass-signal), R078 (DOE
resolution/Monte-Carlo validity), R062-R068 (all 7 Product Chiefs), and
R083-R088 (all 6 Distinguished Experts) -- 20 new contracts total, taking
100_role_L2 from 73/100 to 93/100. Every one follows the same pattern this
section named: a real formula or a real antipattern-guarding boolean check,
never a fabricated threshold, with all four golden-case kinds (positive/
counter_hypothesis/boundary/negative) hand-verified.

## P5.2 — Honest boundary: some roles may never need a domain contract
**Requires:** roles that are inherently judgment/oversight/desk-research
roles (Chief Council, competitive benchmark, patent research) are not forced
into a fake "bounded execution" just to move a percentage. The maturity
rubric's L1 ("complete referenced contract") may be the honest ceiling for
some of these without a real physical/analytical capability behind it.
**Status: held, and re-confirmed after P5.1's sweep.** Competitive benchmark
(R086) and patent research (R087) turned out to still admit a real bounded
antipattern-guard (matched-SPL / claim-element-mapping) without needing to
fabricate a physical measurement, so they were completed under P5.1 instead
of being left at L1. The 7 Chief Council roles (R001-R004, R006-R008) remain
the honest boundary: they synthesize/arbitrate across other roles' outputs,
which is not the same shape as a single bounded analytical check, and are
deliberately left at their current maturity rather than forced.

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
**Status: done -- accepted via an equivalent-value alternative, 2026-09-13.**
The literal requirement (per-skill `golden.json` files in that specific
8-field, multi-case shape) remains exactly as architecturally blocked as
described below: `cases.fixtures()` yields one fixture per skill by
construction, and broadening it means changing every consumer of that
single-fixture contract at once -- a real, shared-module design change, not
one to rush. Rather than invest in that rebuild, the Human explicitly
reviewed the tradeoff and accepted `tests/test_catalog_analytic_invariants.py`'s
100%-breadth additive coverage (independently re-derived, multi-point
regression checks for all 42 of 42 shared-catalog skills -- see below for
the three re-derivation strategies used) as satisfying this item's actual
intent: catching regressions a single golden point would miss. Wired into
`progress_verify.CHECKS["P5.4"]`, which verifies both the 42/42 coverage
and that the test suite itself passes.

Audited 2026-09-13: all 42 shared-catalog skills' `golden/engineering/*/*/golden.json`
files already carry every one of the 8 required fields (verified
programmatically, zero files missing any field). All 93 domain-execution-
contract roles' `golden/roles/R0XX/golden.json` already carry the full
4-case shape (positive/counter_hypothesis/boundary/negative). So field
*correctness* is done everywhere it applies.

What's actually missing is case *breadth* for the 42 shared-catalog skills,
and it turns out to be an architectural constraint, not a content gap:
`golden/engineering/*/*/golden.json` is not hand-authored or independently
extensible -- it is a **derived artifact**, regenerated verbatim from the
single fixture dict returned by `cases.fixtures()` for that skill_id
(`factory.py`'s `materialize()`: `write(ROOT/golden_ref/"golden.json",
{**fixture, "sha256": catalog.digest(fixture)})`). `catalog.definitions()`
asserts `set(result) == set(HANDLERS)`, i.e. **exactly one fixture per
skill**, not a list. Broadening this to a 4-case suite (matching the role
golden shape) means changing `cases.fixtures()` to yield multiple cases per
skill and changing every consumer that assumes a single fixture
(`factory.evaluate_role`'s golden/negative/regression check, `run-skill`'s
CLI, the Skills Library's teaching-example endpoint, the knowledge-corpus
builder) to iterate a list instead. That is a real design change touching
the shared `catalog.py`/`cases.py` module every one of the 42 skills
depends on at once -- correctly out of scope for a single tick, and risky
to rush without dedicated review, unlike the additive, per-role
domain-contract work this session otherwise did 19 times without incident.

**A safe, bounded step taken across this session:** `tests/test_catalog_analytic_invariants.py`
independently re-derives each skill's underlying physical/statistical
formula in the test itself (never sourced from the fixture or copied
from the implementation's own code) and checks it holds at several
points across the input space, not just the one point the shared
golden fixture already covers. Three re-derivation strategies were
used depending on what the skill computes:

1. **Closed-form textbook formulas** re-derived from first principles
   and checked at multiple constructed points (e.g. Butterworth
   unit-DC-gain, `fs = 1/(2*pi*sqrt(Mms*Cms))`, Johnson-Nyquist
   thermal noise, the Zwicker Bark scale, Hagen-Poiseuille flow,
   GUM's law of propagation, the Delany-Bazley absorption model).
2. **Mathematical identities of the definition itself**, constructed so
   the answer is unambiguous by geometry/algebra rather than computed
   (e.g. array power at the exact steering angle must be exactly 1;
   a perfectly linear phase response has one true constant group
   delay everywhere; data on an exact line has `|pearson_r|=1` and
   zero standard error; a maximin policy's answer on a symmetric grid
   is the midpoint; broadside beamforming zeroes every delay).
3. **Known-ground-truth construction** for skills whose own algorithm
   (FFT cross-correlation, least-squares harmonic fitting, ridge
   regression, Gram-Schmidt-orthogonal artifacts) is too complex to
   re-derive point-by-point -- instead the input is built so the
   correct output is knowable by construction (e.g. an impulse pair
   with a chosen integer sample shift for gcc-phat-tdoa; a signal
   built purely from known harmonics for harmonic-noise-analysis; an
   exact linear target under training-set standardization for
   local-audio-regression), then checked against that known truth.

This adds genuine multi-point regression coverage without touching
`cases.py`/`catalog.py`'s single-fixture contract at all -- it's a
wholly separate, additive test file, hand-verified by direct execution
before every assertion was written. **As of this session it covers all
42 of 42 shared-catalog skills** across all 6 suites (DSP x8, Speaker
x7, Product x8, Microphone x7, Array x3, Failure x9 -- see the file's
class-level docstrings for the specific derivation used per skill).

**Update, 2026-09-13: the Human decided.** This was raised as an explicit
scope/definition question -- the blueprint's literal requirement is broader
*golden suites* (`golden/engineering/*/*/golden.json` files each carrying
multiple cases in the specific 8-field shape), which remains exactly as
architecturally blocked as described above: `cases.fixtures()` yields one
fixture per skill by construction (`catalog.definitions()` asserts this),
and broadening it means changing every consumer of that single-fixture
contract at once (`factory.evaluate_role`, `run-skill`, the Skills Library,
the knowledge-corpus builder) -- a real, shared-module design change,
correctly not rushed. The Human reviewed both options (invest in that
rebuild, or accept the additive test file's equivalent regression-safety
value) and chose to accept the additive approach rather than the rebuild.
`progress_verify.CHECKS["P5.4"]` is now registered accordingly, verifying
both the 42/42 skill coverage and that the test suite passes -- see the
top of this section for the accepted status.

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
**Status: satisfied.** P1.4's capability graph shows per-role maturity at a
glance; P4's Skills Library shows the full skill catalog with reachable
teaching examples; a later session's Progress Center rebuild
(`ui/web/progress.html`) added a phase-by-phase visual (ring chart + colored
bars) so the whole P0-P6 blueprint's real coverage is visible on one page,
not just the capability layer. Together these satisfy section 12's "see
real coverage at a glance" requirement.

## P5.7 — Reviewer allocation actually challenges results (Core engineering criterion)
**Requires:** the full loop in the parent spec's final section: requirement
-> specialist selection -> method -> free local analysis -> Evidence ->
verify -> **independent Reviewer challenges the result** -> correct/refine
-> report -> reproducible Knowledge. The "independent Reviewer challenges"
step is the same mechanism P3.6 found is not yet real (no code path sets
`role_l3_accepted` True).
**Status: done, per the Human's explicit decision** ("L3: AI 做審查整理，
真人做最終核准"). `aeris_runtime/engineering/l3_award.py` implements exactly
this: `prepare_review()` packages an already-sealed `challenges.run()`
receipt (which already runs the full requirement -> method -> Evidence ->
independent-reviewer-challenge -> reproduction loop this item names) into a
review packet; `human_decide()` is the *only* code path that can ever set an
L3 grant, and it requires a named Human approver and re-verifies the backing
evidence on every status check (fail-closed). Every pre-existing
`role_l3_awarded: False` self-report in `domain_review.py`/`challenges.py`
is untouched -- this ledger sits beside them as an independent Human-decision
record, not a change to what the AI is allowed to self-certify. CLI:
`aeris l3 pending|prepare|status|award|revoke|verify`. Tests:
`tests/test_l3_award.py`.

## P5.8 — Total-count accounting (section 13's "final report" requirement)
**Requires:** total roles, L0-L4 counts, total executable skills/methods/
golden/negative/regression cases, per-group coverage, unresolved gaps --
all as a real, re-derivable report, not prose.
**Status: done.** `GET /api/v1/capabilities` returns all of these fields
live; `progress_verify._check_p5_8` asserts every required field
(`total_roles`, `maturity_counts`, `total_executable_skills`,
`total_methods`, `total_golden_cases`, `total_negative_cases`,
`total_regression_cases`, `coverage_by_group`, `unresolved_capability_gaps`)
is present on every re-run.

## P5.9 — Do not stop at green tests
**Requires:** treating `100_role_L2 = 100/100` as the real bar, not "tests
pass" or "percentage looks good."
**Status: acknowledged and tracked** -- 93/100 is the honest current number
after P5.1's sweep, not rounded up to 100. The remaining 7 (P5.2's Chief
Council roles) are disclosed as a deliberate, by-nature boundary, not a gap
still being worked -- `100_role_L2 = 100/100` is not this factory's real
achievable bar for roles that are inherently cross-cutting judgment, and
this document says so plainly rather than quietly redefining the bar to
declare victory.

## Sequencing (updated after P5.1's sweep)
P5.1, P5.3, P5.5, P5.6, P5.7, P5.8 are all done; P5.2/P5.9 are honest,
by-nature boundaries rather than open work. The one remaining real gap is
P5.4 (broadening golden-suite coverage further) -- large content work like
P4.4, not a single-tick item, and not faked here.

## Addendum (2026-09-19) — skill-depth expansion beyond the P5.1 L2 minimum

P5.1's `100_role_L2=93/100` counts a role as L2 the moment its *first*
domain skill is evidenced. That threshold says nothing about whether a
role's one skill is actually on-mission (several were found borrowed from
an unrelated product/screening domain, e.g. R069 Psychoacoustics had only
a hearing-aid-boundary review) or whether a role has any real breadth
beyond that single skill. A separate, explicit user request ("100 位聲學
工程師都要在本地可展現出不重複屬性且各自極度廣度和深度的技能深度強化")
started a second, orthogonal effort: giving roles a genuine SECOND (or
third) domain skill, chosen and verified independently of the first,
rather than raising the L2 count itself.

Current state (live-verifiable via
`aeris_runtime.engineering.professional_profiles.ROLE_DOMAIN_CONTRACTS`,
see README.md section 20.1 for the exact command): **37/100** roles now
carry 2 or more independently hand-verified domain skills (one role,
R079, has 3); 56/100 still have exactly one; the 7 Chief Council roles
(R001-R004, R006-R008) remain at zero domain contracts, unchanged from
P5.2's disclosed boundary.

Every added skill follows the same discipline as the rest of this
document: the underlying formula is hand-verified against independent
worked examples *before* any code is written (models that could not be
verified with confidence -- Zwikker-Kosten thermoviscous ports,
Ingard-Rayleigh mesh impedance -- were explicitly rejected rather than
guessed), gets its own manifest/schema/method/golden-suite/unit-test set,
and is re-sealed through the same `scripts/run_capability_factory.py` +
`RoleAcceptanceFactory` pipeline this whole document describes. Several
candidates were investigated and *rejected* after reading the existing
skill's actual source (not just its name or the role's mission text)
showed the proposed addition would duplicate work already present --
R009/R011/R040's sealed/ported-box alignment and array grating-lobe
limit, and R089/R090/R094's standards-edition and Bayesian-hypothesis
logic, were all found already implemented to a more sophisticated degree
than what was being proposed. This is tracked as ongoing content work,
not a new blueprint phase -- it does not change P5.1's L2 count or this
document's P5.1-P5.9 status.
