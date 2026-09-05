# H0001 bounded microphone-array checkpoint — not complete

R037 now executes a sampled far-field uniform-linear-array taper/steering model.
R034 independently recomputes its assertions using real in-phase/quadrature
projections rather than calling the executor. The exact assumptions and model
limits are in `H0001_ARRAY_BEAM_PLAN.md`.

The implementation preserves nominal gain/delay errors, triangle-inequality
gain/delay/position uncertainty, desired-response bounds, sampled sidelobe bounds,
spatial-sampling and far-field guards, grid-gap policy, and white-noise gain for
explicit uncorrelated equal-variance input noise. It rejects unsupported covariance,
invalid geometry/units/nonfinite data and false physical/continuous-pattern claims.

Each role has 15 authored role-specific acceptance cases. Integration executes
actual SQLite workflows, selects R034 as R037's independent domain reviewer,
seals review evidence and reproduces execution. A nominally good design with
insufficient conservative WNG remains `DESIGN_REVISION_REQUIRED`.

Independent review found a subnormal-weight underflow in reviewer variance.
Normalizing coefficients before multiplication/squaring fixes it without imposing
an artificial positive lower weight limit. Scales 1e-200, 5e-324 and 1e6 preserve
variance 0.5 and WNG 2; falsifying WNG to 3 is still rejected. Both 15-case suites
passed the independent follow-up review; the focused integration set passed 19
tests. These are bounded analytical/synthetic L2 scopes, not whole-role L3 or L4.

Source inventory after this checkpoint: 65 engineering Skills/Methods (42 shared
plus 23 domain/reviewer), 23 role suites, 280 role cases. Seventy-seven roles still
lack a domain acceptance suite. Product-specific depth is still limited to R048;
no new Product Chief acceptance or external professional knowledge is claimed.
The prior 204 knowledge entries remain 78 AERIS_AUTHORED, 84 SYNTHETIC and 42
GENERATED_DERIVATION, with zero external-source documents.

Do not promote live maturity from these source counts. Existing production
qualification receipts may be stale after source changes and must fail closed.
The live port-8765 supervisor has not been replaced by this checkpoint. Final
H0001 depth, clean-machine CI, deployment and acceptance remain unfinished.
