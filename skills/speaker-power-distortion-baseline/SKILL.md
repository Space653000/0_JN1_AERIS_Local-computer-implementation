---
name: speaker-power-distortion-baseline
description: Assess speaker harmonic distortion, level compression and a constant-power thermal model against explicit requirements; distinguish thermal and nonthermal follow-up experiments.
---

# Speaker nonlinear / power baseline

1. Read the manifest's Method and input schema. Supply same-frequency,
   same-fixture RMS pressure observations at a reference and elevated voltage.
   Keep true electrical input power separate from apparent VA.
2. Invoke `aeris_runtime.skills_runtime.run_skill` with this Skill ID and the
   declared inputs. Invalid units, absent fundamental, nonfinite values and
   undeclared fields must stop execution.
3. Report THD, pressure-gain compression and estimated coil temperature with
   separate margins and required revisions. A failed requirement requires a
   discriminating experiment; a candidate mechanism is not an established cause.
4. Retain input provenance, Method/source hashes and outputs in the workflow's
   sealed Evidence. Role acceptance requires its separate suite and reviewer.

Scope: FREE_LOCAL_BASELINE, constant-power single-node thermal RC. Supplied
harmonic RMS amplitudes exclude the fundamental and must refer to the same
record/bandwidth. This method does not acquire instruments, infer calibration,
prove lifetime, estimate nonlinear parameters or establish standards conformance.
Limits are caller requirements, not invented IEC clauses. Temperature is a model
estimate, not a measured coil temperature or a safety authorization.
