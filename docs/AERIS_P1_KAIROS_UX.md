# P1 — Kairos-style UX (concrete acceptance criteria)

Codex's `config/progress_truth.v1.json` reserves ids P1.1–P1.8 with no written
definition anywhere in the repo. This document defines them, grounded in the
Human's original brief (narrow nav / whitespace / teal accent from
雷小蒙's Kairos, tool/memory/workflow transparency from Agent Zero, taught
examples from 哈利說的AI軟體必修課) and in what the running UI already does or
does not do. Each item lists what PASS requires and whether it is already
satisfied by the current implementation (`df63b96` at time of writing).

## P1.1 — Visual language: narrow rail nav, whitespace, teal accent
**Requires:** a narrow icon/label sidebar, generous whitespace, and a single
teal/green accent color used consistently for active states and highlights.
**Status: already satisfied.** `.aeris/core-reference/aeris.css` defines
`--accent:#62c5ba` (light) / `#72d0c5` (dark) and the sidebar in
dashboard/workspace/services.html is exactly this narrow rail-with-labels
pattern. No further work needed unless the Human asks for a different look.

## P1.2 — Cards and categorization for at-a-glance state
**Requires:** the dashboard's current capability/state should be readable from
cards grouped by category, not paragraphs of prose.
**Status: mostly satisfied.** Dashboard/services already use
`summary-card`/`feature-card`/`layer` grids. Gap: the Workspace page's task
list is a flat row list, not grouped by state (draft/running/evidenced/etc.);
low priority, revisit after P1.3.

## P1.3 — Work log (工作紀錄): what the system has actually done
**Requires:** a durable, navigable view of executed actions (not just the last
20 audit rows currently shown in a sidebar list) that a human can scroll/filter
by date and distinguishes verified vs unverified entries.
**Status: gap.** `#auditList` today is a 12-20 row snapshot with no
pagination/filter and no persistent page of its own. **Planned work:** add a
dedicated `/activity` route (or expand the existing dashboard `#activity`
anchor into a full page) backed by `/api/v1/audit` with pagination and a
verified/unverified filter, reusing the existing `audit.py` ledger — no new
storage needed.

## P1.4 — Capability graph (能力圖譜): visual map of the 100 seats
**Requires:** a visual (not just a table) representation of the 100 role
seats, grouped by domain, colored/shaped by maturity state (L0-L4), so a human
can see coverage and gaps at a glance — this is the literal "能力圖譜" the
Human's brief asked for.
**Status: gap.** `capabilities.js` currently renders the 100 seats as a flat
list with maturity counts as chips; there is no graph/map view.
**Planned work:** a grouped-grid or radial layout on the existing
`#capability-factory` panel, colored by `execution_state`/maturity level,
sourced from the already-real `/api/v1/roles` + `/api/v1/capabilities` data —
a rendering change only, no new backend data needed.

## P1.5 — Verification-status distinction everywhere capability is shown
**Requires:** any place capability/skill/role state is shown must visually
distinguish TESTED/VERIFIED from CLAIMED/NOT_IMPLEMENTED/CHECKING, per the
Human's "缺少範例或證據時，不得標示為已驗證" rule.
**Status: mostly satisfied.** `stateClass()` in `aeris-live.js` already maps
HEALTHY/DEGRADED/BLOCKED/FAILED to green/amber/rose pills, and services.html
carries the "禁止虛假綠燈" banner. Gap: the capability-matrix panel's chips
(`capCounts`) are plain, uncolored chips — should reuse the same
green/amber/rose convention for L0-L4 states.

## P1.6 — Agent Zero-style tool/memory/workflow transparency
**Requires:** the user can see what tools/skills were invoked for a given task
and the workflow state machine it went through (draft → ready → running →
executed → evidenced → verified → approved → released), not just a final
answer.
**Status: partially satisfied.** The workspace page's `#workflowRuns` list and
the 8-step `.timeline` component already expose this. Gap: there's no drill-in
from a task to its own step-by-step timeline; today the 8-step timeline is
generic/decorative, not bound to a specific task's real state history.

## P1.7 — 哈利說的-style taught examples: interactive skill walkthroughs
**Requires:** every skill/capability surfaced in the UI links to a Traditional
Chinese example with expected result, and reproducible/synthetic examples are
visually distinguished from real engineering acceptance (the Human's explicit
"教學展示、合成資料與真實工程驗收必須清楚區分" rule).
**Status: gap, but partially scaffolded.** `capabilities.js`'s workspace panel
already has a "載入合成 黃金 案例" (load synthetic golden case) button and
labels synthetic vs user-supplied data sources — that half exists. Missing:
a plain-language walkthrough/expected-result panel per skill, not just a raw
JSON fixture loader.

## P1.8 — 繁中 explanation copy is plain language, not jargon
**Requires:** UI copy avoids unexplained jargon; where a technical
term (G0-G5, L0-L4, R0-R4) is unavoidable, a one-line plain-language
gloss is available on demand (tooltip/expandable), not assumed knowledge.
**Status: gap.** Current copy uses G0-G5/L0-L4/R0-R4 freely with no inline
glossary. **Planned work:** a small glossary dictionary + `title`/tooltip
attachment pass over these badges, reusing the existing `i18n.js`
infrastructure (same pattern as the EN/zh-TW toggle) rather than new
mechanism.

## Sequencing
P1.1/P1.2/P1.5 are already substantially done (verify, don't rebuild). Real
remaining work, roughly in order of value and how directly they touch already
real data with no new backend needed: P1.4 (capability graph rendering) →
P1.3 (work-log page) → P1.6 (task-bound timeline) → P1.8 (glossary) → P1.7
(taught-example panel, most content-heavy).
