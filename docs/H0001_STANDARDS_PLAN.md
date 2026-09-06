# H0001 supplied standards metadata applicability baseline

R089 owns edition/scope/provenance and change-impact reasoning. R090 reviews
requirement/certification traceability without granting customer or regulatory
approval. The existing standards registry remains the discovery source; do not
invent a current edition for entries whose edition/source is unknown.

## Deterministic metadata assessment

Accept explicit previous/current metadata snapshots and a pinned as-of timestamp,
not ambient clock time during reproduction. Require family, edition, region and
domain scope, declared CURRENT/SUPERSEDED/UNKNOWN status, superseded-by reference,
normative/informative classification, publisher, source URL, retrieval timestamp,
access/license status and linked requirement IDs. Unknown fields remain unknown;
public metadata availability is not permission to import licensed normative text.

Each supplied source record includes embedded metadata content and its canonical
SHA-256. Validate exact byte/content identity, but never infer authenticity, a
live fetch or real current-edition verification from a hash or supplied label.
Synthetic scenarios use explicitly fictitious families and reserved example
URLs; no fabricated citation to an actual standard. Real registry entries with
missing data produce visible metadata gaps, not invented fields.

For a declared requirement context, calculate distinct scope applicability,
metadata completeness/freshness, declared licensing sufficiency for the intended
metadata-only versus normative use, and change-review disposition. Explicit
region and domain exclusions are NOT_APPLICABLE only when scope is known;
missing scope is UNKNOWN, not NOT_APPLICABLE. Metadata-ready is not formal
conformance, professional-tool verification, customer approval or Human review.

Pin a documented freshness interval and reject future/unzoned timestamps.
Superseded or unknown status cannot be metadata-ready. Same-family previous and
current snapshots yield a field-level change list and exact linked requirement
IDs needing re-review. Requirement IDs and family mappings are independently
declared; don't infer them from only surviving links. A change cannot silently
be accepted because a supplied PASS flag says so.

Separate semantic changes (edition, status, superseded-by, region/domain scope,
normative classification, access/license and requirement mapping) from retrieval
or provenance changes (source record, retrieval timestamp, source URL/publisher,
content identity). A same-content refresh improves only freshness; it neither
creates new semantic change-impact nor clears an existing previous-to-current
semantic re-review disposition. Preserve semantic blockers after every refresh.

Impacted requirement IDs include the union of previous and current mappings and
scope eligibility. A requirement moved out of current scope must still be listed
if it was previously in scope; unknown prior scope conservatively retains its
family-linked requirements. The immutable external requirement list supplies the
denominator, not whichever links survive in the new snapshot. Provenance changes
remain independently visible and never verify source authenticity.

## Roles and company challenge

Independent R089 scenarios cover edition drift, region exclusion, unknown scope,
normative versus informative access, stale source, superseded metadata and
requirement impact. R090 independently checks exact metadata blockers, impacted
requirements and false certification/provenance assertions. No role-wide L3.

Company Challenge starts with a stale supplied source snapshot; revised input
adds a newer explicitly synthetic metadata retrieval for the same declared
family/edition/scope. As-of time, intended use, requirements, licensing policy,
all unchanged content and previous snapshot remain fixed. The added retrieval
record is hypothetical and cannot turn live_verified or formal_conformance true.
Bind the revision to the same sealed initial task and preserve old snapshot
provenance; require exactly the allowed timestamp/source-record update, not an
arbitrary new edition or relaxed scope. Run actual SQLite/Pod/workflow/independent
review/Evidence/report/Memory/reproduction with negative origin substitutions.

Before implementation, resolve taxonomy, provenance authenticity boundaries,
unknown versus exclusion, requirement denominator and allowable revision scope.
Keep Core and PR32 immutable and all raw/local evidence private.

## Isolated plan review correction

Addressed P2: fixed semantic versus retrieval/provenance classifications and
refresh monotonicity above. Add independent oracles for same-content freshness
without semantic impact, edition drift still requiring review after refresh, and
requirements removed from current scope remaining in the impact union. A fresh
timestamp cannot resolve edition/scope disagreement or imply live retrieval.
