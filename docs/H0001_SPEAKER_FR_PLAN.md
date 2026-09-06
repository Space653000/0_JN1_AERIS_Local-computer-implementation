# H0001 speaker FR requirement decision

Next bounded domain: R015 speaker measurement evaluates supplied frequency/SPL
samples against an explicit requirement envelope and measurement validity.
R079 independently reviews conservative uncertainty and reference normalization.
This closes one additional company Challenge seam, not whole speaker expertise.

## Method boundary

Inputs carry strictly increasing positive frequency, supplied SPL at measured
distance and drive with explicit positive lower/upper bounds, declared exact
reference distance/drive targets, lower/upper requirement arrays, conservative
level uncertainty excluding those separately declared distance/drive bounds,
time-window duration, minimum observable
cycles and a declared free-field far-field model. All arrays have equal bounded
length. No calibrated acquisition, complete-band coverage or standards conformity
is inferred. Invalid units, nonfinite values, crossed envelopes and unsupported
propagation models reject before execution.

Normalize SPL to the declared reference with 20log10(distance/reference distance)
and 20log10(reference voltage/measured voltage). Require declared linear small-
signal operation, identical configuration and gain path, and no compression,
clipping, AGC or limiter for this voltage scaling. Unknown/contradictory model
declarations reject; declarations are assumptions, not measured linearity proof.
Normalize the lower interval with distance lower / drive upper, and the upper
interval with distance upper / drive lower, adding the supplied level bound.
Bounds must contain the nominal measured values and remain strictly positive.
Treat supplied uncertainty as a worst-case interval, not statistical confidence.
Each sample
must meet its envelope across that interval and have frequency * gate duration
at least the declared required cycles. Undersampled/gated low-frequency points
are INSUFFICIENT_MEASUREMENT_VALIDITY rather than a trustworthy acoustic failure.
Never interpolate a few samples into a full-band conformity claim. Revision
advice distinguishes insufficient window, uncertainty crossing and actual
sampled response outside limits; no automatic EQ or physical causation claim.

## Independent acceptance

Author R015 scenarios for reference distance and voltage normalization,
window-limited low frequency, envelope boundary, uncertainty-induced rejection,
and equal apparent deficits caused by normalization versus actual response.
R079's different questions challenge unpropagated uncertainty, inverted bound,
wrong reference sign and mistaken statistical/physical certification claims.
Include nominal PASS but distance/drive propagated bounds crossing FAIL, invalid
reference intervals and distance-valid but voltage-nonlinear rejection cases.
Separate reviewer calculations must not call the executor to generate expected
answers. Include wrong-claim and corrected-claim cases, input negatives and
sealed qualification replay. Both scopes remain L2; no automatic L3 or L4.

## Integration and gates

Add Skill/Method/role suite bindings to the existing domain factory, profile,
review selection and sealed workflow seams. Then implement SPEAKER_FR in the
company challenge registry: initial short time window, longer revised window,
same SPL values, unchanged mask/uncertainty/cycle requirement. This is a changed
hypothetical observation window, not a measured product improvement. Independent
oracles require initial invalidity and revised sampled-mask acceptance.

Tests must prove misnormalization, uncertainty undercoverage, invalid gates,
wrong reviewer and missing reference claims fail closed. Preserve all prior
domain regressions, full local tests and six-page availability. Keep source/test
artifacts local, Core read-only and PR32 unchanged. No remote writes in this batch.

## Isolated plan review disposition

Accepted P1: separate distance and drive bounds from the level budget; explicitly
propagate all three through normalization with exact target coordinates.
Accepted P2: free-field propagation does not imply linear drive scaling; declare
and enforce the separate small-signal/configuration/gain-path applicability and
preserve it as an assumption, never measured proof. Both have negative/oracle
cases above. Same-model isolated review is not qualified Human approval.
