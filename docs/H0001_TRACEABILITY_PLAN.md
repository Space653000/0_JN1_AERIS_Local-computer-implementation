# H0001 versioned requirement and evidence-link baseline

R097 owns requirement/test/evidence/configuration linkage, not the acoustic test
algorithm or customer approval. R099 independently challenges orphaned links,
stale revisions, incorrect denominators and unsupported evidence claims. This is
a bounded local software contract; it cannot certify product conformance.

## Model and scope

Inputs explicitly enumerate required requirement IDs/revisions and quantitative
lower/upper bounds with units, test ID/revision, and target product/configuration
revision. Every required requirement remains in the coverage denominator even
when it has no test. Duplicate IDs, dangling references and ambiguous mappings
fail closed rather than being silently deduplicated or substituted.

Each requirement also declares its immutable, nonempty required test ID/revision
set independently of actual links. ALL means every declared association must
exist and pass; never infer the expected set from supplied links. Track both
requirement-level coverage and required-association coverage, so linking only one
of two mandatory tests cannot count as complete. Reject duplicate expectations.

Requirement and test definitions both pin measurand and reference identity, not
merely display units. Results must match these exact identities and units; no
implicit conversions. One result can support multiple requirements only when
their expected test/revision and measurement semantics are identical. Distinct
limit values may legitimately evaluate the same matching result differently.

Test result records carry supplied numeric observation, symmetric uncertainty
bound, unit/reference, test revision, product/configuration and source record ID.
An embedded canonical result payload has a declared SHA-256 that must match its
actual bytes/defined canonical serialization. A valid hash establishes content
identity only: no signature, source authenticity, calibration or physical
measurement is inferred. Synthetic and supplied-unverified sources are separate.

Links bind requirement revision, expected test revision, exact result digest and
configuration revision. Missing links, stale or mismatched revisions, orphaned
results, wrong units/reference, failed result status and reuse incompatible with
the named test remain explicit. Multiple tests for one requirement must all pass
unless the requirement explicitly declares another combination rule; first
implementation uses ALL only and rejects unsupported alternatives.

Independently recompute numerical requirement disposition from observation and
uncertainty, not a caller's PASS flag. Entire uncertainty interval inside bounds
is a bounded synthetic/supplied-input policy pass; crossed bounds are unresolved
or failed, never rounded into physical acceptance. Declare representation policy
separately from supplied uncertainty. Every decision includes the exact linked
requirement/test/result/configuration revisions and reason codes.

Coverage fields distinguish linkage completeness, current content hash identity,
bounded numerical interval satisfaction and verified real measurement evidence.
The last count stays zero unless a separate authorized physical-evidence system
actually verifies it. All source records in this tranche are synthetic or
supplied unverified. Empty requirements cannot produce a vacuous 100% or PASS.

## Company challenge and independent acceptance

Use two required quantitative checks, one initially unlinked. Revision adds one
link to an already supplied matching test result; requirement/test definitions,
limits, configuration and every previous link remain immutable. Missing coverage
becomes complete linkage, not a newly acquired physical measurement. Run actual
SQLite task, Pod, Method, sealed input/results, R099 review, Memory and reproduction.
Link-addition semantics must be checked before second execution and during status;
changing a requirement bound or substituting a new result is not this challenge.

Role suites independently cover missing denominator entries, stale requirement
and test revisions, wrong configuration, mutated payload hash, false physical
claim, duplicate/dangling links, exact interval boundary and genuine exceedance.
R099 uses independent indexing/interval assertions and challenges the complete
output, not just percentage totals. Both roles stay bounded L2. No universal
reviewer role, customer certification, signed artifact or whole-role L3 is claimed.

Before implementation, review ambiguity around many-to-many links, content hash
versus authenticity, unit references, immutable revision origin and physical
acceptance language. Core and historical PR32 remain untouched.

## Isolated plan review corrections

Addressed P1: immutable required associations are independent of actual links,
with separate denominators. Add two-required-tests/one-link and deleted-required-
association challenge regressions. Addressed P2: pin measurand/reference on all
three sides, with same-unit/different-reference, different-measurand and valid
many-to-many reuse oracles. This review is not Human acceptance.
