# P4 — Skill Teaching (concrete acceptance criteria)

Like P1-P3 before it, `config/progress_truth.v1.json` reserves ids P4.1-P4.7
with no written definition. This document defines them, grounded in the
Human's original brief: 哈利說的AI軟體必修課's requirement that "所有技能必須
有繁中教學範例與預期結果...教學展示、合成資料與真實工程驗收必須清楚區分。缺
少範例或證據時，不得標示為已驗證" -- every skill needs a Traditional-Chinese
taught example with an expected result, clearly separated from real
engineering acceptance, and P1.7 already built exactly this rendering for a
single skill (tied to a workspace role selection). P4 is scaling that from
"one skill you happen to select while creating a task" to "the full 132-skill
catalog, browsable on its own."

## P4.1 — A browsable Skills Library, not just a per-task fixture loader
**Requires:** every skill in `GET /api/v1/skills` (132 as of this session) is
listed somewhere a human can browse and search, not only reachable by first
picking a role and task in the workspace.
**Status: this session's target.** Extends `capabilities.js`'s services-page
section with a searchable skill list reusing the existing P1.7
`renderTaught` panel per skill.

## P4.2 — Every skill's taught example is reachable in one click
**Requires:** from the Skills Library, one click shows the same
reason/expected-result/negative-example walkthrough P1.7 built, for whichever
skill was clicked, not just the one skill a workspace task happens to need.
**Status: this session's target**, same mechanism as P4.1.

## P4.3 — Honest coverage accounting: not every skill has a golden fixture
**Requires:** skills without a reachable golden fixture for their mapped role
report that plainly, not a blank/broken button.
**Status: this session's target.** The Skills Library must show "no example
available" rather than a silent failure when `/fixture` 404s.

## P4.4 — zh-TW plain-language skill descriptions
**Requires:** skill descriptions in the library are in Traditional Chinese,
consistent with the rest of the zh-TW-first UI, not raw English `acceptance`
strings from the manifest.
**Status: gap, partially addressed.** Skill manifests only carry English
`acceptance`/`applicability` strings; a full zh-TW translation of all 132
skills' descriptions is a large content task (like en.json but the reverse
direction and much bigger), not done this tick. The library will show the
English source honestly rather than a fabricated translation, and this gap
is disclosed rather than silently shipped as "done."

## P4.5 — Wire coverage into `aeris_runtime.progress_verify`
**Requires:** "how many of the 132 skills have a reachable taught example" is
a reproducible check, like P3's role-L2 coverage.
**Status: this session's target**, once P4.1-P4.3 land.

## P4.6 — Distinguish skill-level teaching from role-level capability
**Requires:** a skill's taught example (this phase) is visibly a different
concept from a role's capability-graph maturity level (P1.4/P3) -- teaching
material is not evidence of role acceptance.
**Status: satisfied by construction.** The Skills Library is a new,
separate UI section from the Capability Matrix graph; nothing in it writes
to or reads `current_maturity_level`.

## P4.7 — Real content, not placeholder text, for the highest-traffic skills
**Requires:** whatever is shown is real fixture/check/reason data (same
honesty bar as P1.7), not lorem-ipsum placeholders, for at least the most
commonly role-mapped skills.
**Status: satisfied by construction** -- the Skills Library reuses the exact
same `/api/v1/capabilities/fixture/{role}` data source as P1.7, so there is
no separate "placeholder content" path to accidentally ship.

## Sequencing this tick
P4.1-P4.3 (browsable library + reused teaching panel + honest no-fixture
disclosure) are the concrete build. P4.4 (full zh-TW translation of every
skill description) is real but large content work, explicitly deferred and
disclosed rather than faked. P4.5 follows once the UI exists to check
against. P4.6/P4.7 are satisfied by how P4.1-P4.3 are built, not separate
work.
