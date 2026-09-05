# H0001 two-channel TDOA and geometry challenge

R043 owns a bounded two-channel GCC-PHAT estimate from actual supplied sample
arrays. R040 separately reviews delay/geometry/ambiguity and numerical assertions.
This is neither a complete beamformer nor a physical microphone-array acceptance.
It advances the ARRAY_DOA Challenge; other array and far-field work stays visible.

## Signal and physical contracts

Use equal finite bounded real vectors, explicit sample rate, ordered channel
orientation, analysis band, microphone spacing interval, speed-of-sound interval,
minimum spectral excitation and declared timing/peak separation bounds. Require
an explicit far-field plane-wave, synchronized linear two-channel assumption.
Unknown geometry/clock/model declarations reject; they are not measured proof.
All temporary signal/evidence/plot data remains under local .aeris.

Demean, zero-pad to cover linear correlation, band-limit cross spectrum and
apply PHAT only to supported nonzero excited bins. Silent/insufficient-band data
reject, not a zero-angle estimate. Define positive lag as channel 2 arriving
after channel 1. Search the full linear-correlation lag domain first; do not
silently pick an unrelated smaller peak merely because the dominant arrival
lies outside the physical spacing/sound-speed bound. Report competing peaks and
the declared peak-separation criterion. Ambiguous candidates remain unresolved.

Fix the polarity contract to SAME_POLARITY. Score absolute GCC magnitude over
the full lag range so an inverted dominant arrival is detected rather than
missed; a negative signed dominant peak makes the model/polarity unresolved.
Define the contiguous main-lobe support around the maximum using an explicit
support_fraction of that maximum. Exclude that support and the explicit integer
peak_exclusion_samples guard before finding the strongest competing score.
Declare minimum_peak_ratio > 1 and maximum_support_width_samples. Equal dominant
scores within declared numerical resolution are unresolved, regardless of the
deterministic tie-break used to report lag. The ratio requirement is inclusive;
an over-wide single main lobe is also unresolved, not a unique narrow peak.

Geometry review checks spatial aliasing at the declared band ceiling, physically
admissible lag, sample-time uncertainty (at least half a sample), spacing/sound-
speed intervals and angle ambiguity. A linear pair cannot resolve front/back or
3D cone ambiguity: report a broadside direction-cosine interval and explicitly
bounded planar angle candidates, never a unique 3D source direction. An interval
crossing the physical direction-cosine domain is unresolved, not clipped to a
confident endfire estimate. Echo/reflection and channel-order counter-hypotheses
remain separate next experiments. No real DOA/calibration claim is possible.

Delay intervals use the entire qualifying contiguous main-lobe support plus the
declared timing bound (minimum half a sample) and a separate required supplied
estimator_error_bound_samples. The latter is an unverified modeling bound, not
estimated confidence. A broad/flat main lobe fails the width criterion instead
of receiving a half-sample-only angle interval. Reviewer uses the same declared
band mask/PHAT/support contract with separate numerical recomputation.

## Acceptance and independent review

Author deterministic synthetic broadband delayed signals, zero-lag and reversed
channel cases, an out-of-aperture dominant lag, ambiguous two-arrival data,
insufficient excitation, aliasing, uncertainty crossing and malformed inputs.
Known synthetic lag and geometry equations supply independently worked oracles;
fixtures are not generated from the estimator output. R040 challenges incorrect
lag sign, unsupported uniqueness, interval omission and wrong revision advice.
The reviewer separately recomputes correlation with an alternate numerical path
and checks every output assertion, not merely plausible geometry around a
caller-chosen lag. Qualify both seats through actual sealed role suites at L2.

## Company integration

ARRAY_DOA initial data contains competing arrivals, so the workflow must retain
an unresolved/revision-required decision. Revised hypothetical input isolates
one arrival with unchanged geometry, frequency band and acceptance limits.
The real Challenge must execute both workflows, independent review, numerical
verification, report, Memory and reproduction. This is an analytical experiment,
not a physical countermeasure, calibration or whole-role L3 award.

Before source implementation, adversarial review must resolve algorithm/sign,
uncertainty/ambiguity, oracle independence and threshold-scope issues. Then use
red/green tests and the existing sealed Challenge anti-transplant regressions,
full tests and page-availability checks. No Core or GitHub write in this batch.

## Isolated plan review disposition

Both P2 findings accepted: fix peak scoring/polarity/support/separation/equality
rules and distinguish sampling quantization from wider estimator uncertainty.
Add inverted-polarity, equally high separated peaks and single broad-lobe cases
to the independent role oracles; an unresolved peak cannot yield a confident
narrow-angle claim. This remains a bounded model, not a confidence estimator.
