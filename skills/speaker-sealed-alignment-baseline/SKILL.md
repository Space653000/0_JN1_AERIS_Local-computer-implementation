---
name: speaker-sealed-alignment-baseline
description: Ideal sealed small-signal T/S alignment with independent supplied bounds; no ported or excursion acceptance
---

# speaker-sealed-alignment-baseline

Use only for the declared bounded R009 role contract. Validate exact SI units,
ordered parameter bounds and IDEAL_SEALED_SMALL_SIGNAL model before execution.
Run through the AERIS Skill runtime and preserve source/input/output hashes.
Report every policy check, model limitation and counter-hypothesis. Never equate
F3 with Fc except at Butterworth alignment; retain the interior F3 minimum.
The geometry frequency must cover Fc/F3 upper bounds. Synthetic calculations do
not establish calibrated T/S, excursion, ported alignment, role L3 or Human
approval. Qualification uses golden/roles/R009/golden.json, not shared Skill PASS.
