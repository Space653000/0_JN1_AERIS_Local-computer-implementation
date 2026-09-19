---
name: aeris-invariant-check
description: Add one more hand-verified, multi-point regression test to tests/test_catalog_analytic_invariants.py (P5.4 golden-suite breadth) for a shared-catalog skill that doesn't have one yet.
---

# aeris-invariant-check

P5.4 ("expand the Golden Acoustic Factory") is real, large content work
that cannot be done in one tick — see `docs/AERIS_P5_ENGINEER_FACTORY.md`'s
P5.4 section for why `golden/engineering/*/*/golden.json` can't just be
hand-edited (it's a derived artifact, regenerated from a single fixture
per skill in `cases.py`/`catalog.py`, and broadening that to a multi-case
suite is a shared-module architecture change, not a content edit).

`tests/test_catalog_analytic_invariants.py` is the safe, additive
alternative this session established: it doesn't touch the fixture
pipeline at all, just adds independent multi-point regression coverage
on top. This skill is the repeatable procedure for adding one more
skill to that file. As of this writing it covers 6 of 42 shared-catalog
skills across all 6 suites (DSP, Speaker, Product, Microphone, Array,
Failure) — see the file's own class-level docstrings for exactly which.

## Procedure

1. **Pick a skill** not already covered (check the class docstrings in
   `tests/test_catalog_analytic_invariants.py`). Prefer one whose
   `golden/engineering/<suite>/<skill>/golden.json` `reason` field
   describes a clean analytic relationship, not a fitted/empirical one.

2. **Read the implementation**, not just the golden fixture. It's in
   `aeris_runtime/engineering/numerics.py` or `governance.py` (grep for
   `def` near the skill's output field names). Understand exactly what
   formula or algorithm produces each output field you intend to check.

3. **Independently re-derive the expected value — never copy the
   implementation's own math back at itself.** This is the part that
   actually matters; skipping it turns the "test" into a tautology. Three
   patterns have worked so far, in order of preference:
   - **First-principles formula re-derivation**: if the output is a
     closed-form expression (e.g. `fs = 1/(2*pi*sqrt(Mms*Cms))`,
     `20*log10(ratio)` conversions, `ppm*3.6` unit conversion), work out
     the formula yourself from the underlying physics/math, not from
     reading the implementation's code.
   - **Known-ground-truth construction**: if the skill runs a real
     algorithm you shouldn't re-implement (FFT cross-correlation, an
     optimizer, a search), construct an input where the correct answer
     is unambiguous *by construction* — e.g. gcc-phat-tdoa's test builds
     an impulse pair with a manually chosen integer sample shift, so the
     true delay is known without running any correlation algorithm at
     all, and checks the implementation recovers exactly that shift.
   - **Independent closed-form special case**: if the general case
     needs the same external library call the implementation itself
     uses (e.g. `scipy.stats.beta.ppf` for the general Clopper-Pearson
     bound), find a special case with its own independent derivation
     instead (e.g. zero-failures binomial: `p = 1 - alpha**(1/n)`,
     derived from `(1-p)^n = alpha`, not from calling `beta.ppf` at
     all). Document plainly that the general case isn't covered by this
     weaker pattern if you use it.
   - If none of these are tractable with real confidence (this has come
     up for genuine Monte Carlo simulations and other stochastic
     methods) — **skip that skill and pick a different one.** Do not
     force a passing assertion you aren't sure is actually checking
     anything.

4. **Hand-verify by direct execution before writing any assertion.**
   Write a throwaway script (delete it before committing — see the
   pattern used for `scratch_tdoa_check.py`/`scratch_reliability_check.py`
   this session: created in the repo root, run via
   `.venv\Scripts\python.exe <script>.py`, deleted immediately after)
   that calls `aeris_runtime.engineering.catalog.execute(skill_id,
   params)` with 3+ different parameter combinations and compares the
   result to your independently-derived expected value. Only proceed to
   step 5 if every case matches to floating-point precision.

5. **Add a new `unittest.TestCase`** to
   `tests/test_catalog_analytic_invariants.py`, following the existing
   classes' shape: a docstring explaining the re-derivation and why it's
   independent, a small helper method wrapping `catalog.execute`, and a
   single test method using `subTest` to iterate the parameter
   combinations you hand-verified.

6. **Run the file** (`python -m unittest
   tests.test_catalog_analytic_invariants -v`) and confirm every test
   passes, including the ones already there.

7. **Update `docs/AERIS_P5_ENGINEER_FACTORY.md`'s P5.4 section**: add one
   sentence describing the new skill's formula/construction and bump the
   "N of 42 skills" / "N of 6 suites" counts. Do not change P5.4's
   overall status from "not done" — that only changes once this file
   covers a genuinely broad fraction of all 42 skills, which is still far
   off.

8. **Commit and push.** This is a test+docs-only change — it does not
   require restarting the local supervisor (`AERIS_START.ps1`), since it
   doesn't touch any server-side code path. Only restart if you've also
   changed runtime code in the same commit.

## What NOT to do

- Do not register a `progress_verify` check for this file. P5.4 stays
  correctly UNKNOWN in the Progress Truth system until the breadth is
  genuinely substantial — a check here would prematurely mark it PASS.
- Do not batch many skills into one commit. One skill, hand-verified,
  one commit — matches this session's established cadence and keeps
  each change reviewable and revertable independently.
- Do not edit `golden/engineering/*/*/golden.json` directly to "add
  cases" — it's regenerated from `cases.py` and any manual edit will be
  silently overwritten the next time `factory.materialize()` runs.
