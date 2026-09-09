# H0001 microphone array taper and bounded sampled pattern

R037 chooses a uniform-linear-array amplitude taper and steering tradeoff.
R034 independently checks the resulting sampled directional response and the
conservative effect of channel gain, delay and position errors. This does not
claim measured far-field speech, diffuse noise performance or whole-role L3.

## Exact bounded model

Require 2..32 ordered uniform linear elements with explicit spacing, nonnegative
real taper coefficients (not all zero), positive nominal channel gains and known
channel delays. All quantities use SI units. Geometry is x_i=i*spacing; angles
are -90..90 degrees from broadside. Steering is ideal true-time-delay using
nominal positions. Require positive ordered frequencies and sound speed, a
source range, per-element maximum position error, absolute gain error and delay
error, declared far-field and spatial-aliasing policy.

For frequency f and arrival theta, normalized transfer is:

H = sum_i a_i*g_i*exp(j*2*pi*f*((x_i*(sin(theta)-sin(steer)))/c - delay_i)) / sum_i a_i.

Use exp(j*omega*t). A positive arrival angle advances the signal at positive x:
s_i(t)=s(t+x_i*sin(theta)/c-delay_i). Positive channel delay means additional
time delay, not phase advance. Steering subtracts x_i*sin(steer)/c. A nonzero
steering/differential-delay oracle must test both cancellation and reinforcement.

Weights are implementation coefficients, not optimization output. Require noise
covariance sigma^2 I before the declared channel gains: identical variance and
cross-channel uncorrelated noise, not merely temporal whiteness. Unknown or
correlated noise models are unsupported and must be rejected. Nominal output
white noise variance is sum((a_i*g_i)^2)/(sum a)^2, so WNG is desired amplitude
squared divided by that variance. Zero desired response yields WNG=0, not NaN.
This is not diffuse/ambient/SNR or microphone self-noise certification.

Triangle inequality bounds true response under independent supplied errors.
For each element, phase uncertainty is
2*pi*f*(position_error*abs(sin(theta))/c + delay_error).
Bound |g*exp(j*dphi)-gnom| by gain_error +
2*gnom*sin(min(phase_uncertainty,pi)/2), then weight and sum. Clip the amplitude
lower bound at zero; the upper bound may exceed unity. Preserve nominal gain
error and known delay; do not normalize the observed response to its own peak.

Worst-case output noise uses g_i+gain_error_i. Conservative desired WNG uses
the squared desired amplitude lower bound over this upper noise variance.
No positive lower WNG is inferred when the desired gain is unidentifiable.

## Sampling and validity

Evaluate an explicit sorted angle grid spanning -90..90 plus the exact steering
direction. A fixed main-lobe exclusion half-width defines sidelobe samples;
require at least one sample outside it. Do not call the largest sampled sidelobe
a continuous-angle bound. Retain sample grid and maximum angular gap in output.
Policy requires maximum angular gap, target gain lower bound, sampled sidelobe
upper bound and conservative white-noise gain at every requested frequency.

Spatial alias guard requires worst-case adjacent spacing (spacing+2*position
error) <= c/(2*fmax); this conservative condition is not sufficient evidence for
continuous pattern quality. Far-field policy uses worst-case aperture squared,
2*D^2*fmax/c and explicit minimum source-range ratio. Include an absolute
aperture-distance condition to avoid pretending the tiny-array Fresnel bound
alone establishes distant-source validity. These are declared model heuristics.

## Oracles and review

Authored independent cases: two-element broadside unity gain and WNG=2; at
half-wavelength spacing endfire is a null and broadside is unity; taper [1,0]
is omnidirectional with WNG=1 rather than a narrower beam. Four uniform elements
give nominal WNG=4; unequal gains and differential delay spoil an intended null.
Gain/delay/position intervals must widen bounds without becoming measurements.
Validate alias limit, near-field guard, sparse grid, desired-null WNG=0, all-zero
taper, wrong units, reversed angle/frequency arrays and physical-claim mutations.

Independent R034 review should use real cosine/sine sums and direct variance,
not call the executor or derive expected verdict from the candidate. R037 and
R034 have different acceptance questions and own sealed suites. Integrate through
actual SQLite workflow, qualified context-sensitive Pod, sealed review and replay.
Keep all raw runtime artifacts local and do not add a ninth company challenge.
