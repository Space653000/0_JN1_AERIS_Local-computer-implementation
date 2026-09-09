# H0001 sealed-speaker alignment and lumped-model scope baseline

Next priority is acoustic depth, not preserving a maturity number. R009 executes
an ideal sealed-box small-signal T/S alignment. R021 independently reviews the
lumped-model assumptions, parameter-bound propagation and geometric validity.
This deliberately bounded capability does not claim vented-box, large-excursion,
FEM, measured impedance or complete speaker-design acceptance.

## Model and inputs

Require Fs, Qts, Vas and effective Vb nominal values plus independent explicit
lower/upper bounds containing each nominal. Units are Hz and cubic metres. Only
IDEAL_SEALED_SMALL_SIGNAL is supported; reject a ported/leaky/unknown model rather
than reuse the equations. Input bounds are supplied assumptions, not calibrated
uncertainty or inferred manufacturing distributions.

For alpha = 1 + Vas/Vb, compute Fc = Fs*sqrt(alpha), Qtc = Qts*sqrt(alpha), and
the second-order high-pass -3 dB frequency relative to asymptotic gain. Derive F3
from the positive quadratic root in squared normalized frequency, using a stable
root expression. Do not assume F3 equals Fc except at Qtc = 1/sqrt(2).

Preserve the non-monotonic F3 dependence on alpha: the stationary point occurs at
alpha = 1/(2*Qts^2). Endpoint-only sampling is not a justified lower bound.
Use analytic monotonicity in Fs/Qts, alpha endpoint checks and the interior
stationary point when inside the independent parameter interval. Report nominal
and conservative intervals, not a Monte-Carlo confidence claim.

Policy inputs fix maximum F3, acceptable Qtc interval, maximum effective box
volume and geometric model validity. The latter uses largest internal dimension,
declared analysis maximum frequency, sound-speed bound and explicit maximum
dimension/wavelength ratio. Geometry validity is separate from meeting F3/Qtc;
a passing bass target cannot certify the high-frequency lumped approximation.
No excursion, port turbulence, leak impedance, full nonlinear response or real
SPL/power capacity is inferred from the four T/S parameters alone.

The declared analysis maximum must cover both conservative Fc and F3 upper
bounds. If it does not, alignment validity remains unresolved and overall policy
cannot pass. Lowering the frequency to make dimension/wavelength look smaller is
not a valid correction. Use the sound-speed lower bound for worst-case geometry.

## Independent acceptance and integration

R009 cases cover under/over-damped alignment, Butterworth boundary, infeasible
volume, parameter bounds crossing target and an interior F3 minimum. Negative
cases include invalid bounds, wrong model and unsupported unit/field variants.
R021 independently solves/checks the transfer equation and parameter extrema,
including F3!=Fc, false confidence, ignored geometric violation and illicit
excursion/physical-verification assertions. Hand-worked oracles precede code.

Route actual R009 execution to qualified R021, seal source/input/output, produce
an engineering report and reproduce the run. Both seats remain bounded L2 until
their broader profession-specific acceptance and independent authority genuinely
exist. Do not add another company-challenge family merely to inflate the count;
the eight specified families stay fixed. Core and historical PR32 remain intact.

Before implementation, independently review the extrema proof, model geometry
criterion, misleading F3 reference assumptions and numerical root stability.

## Isolated plan review correction

Accepted P2: tie geometry frequency coverage to conservative Fc/F3 results and
add the lowered-analysis-frequency negative oracle. Review confirmed the quadratic,
monotonicity and interior-minimum derivation above; this is not Human approval.
