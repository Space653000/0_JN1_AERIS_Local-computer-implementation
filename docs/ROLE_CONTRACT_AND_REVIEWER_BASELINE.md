# AERIS Role Contract + Independent Reviewer Baseline

## Purpose

AERIS has 100 canonical capability seats. This baseline makes every seat machine-readable without pretending that 100 seat definitions equal 100 domain-verified acoustic engineers.

`config/role_contracts.v1.json` defines the common responsibility/permission/Evidence envelope and the currently available baseline Skills/Methods/Standards metadata. `aeris_runtime/role_contracts.py` materializes exactly 100 deterministic contracts and rejects missing referenced assets.

## Contract truth

Every seat currently has:

- canonical role identity/group/domain;
- allowed and forbidden action classes;
- Evidence/output requirements;
- risk ceiling;
- checked references to current baseline Skills/Methods/Standards metadata;
- deterministic SHA-256 contract fingerprint.

Every seat intentionally remains `CONTRACTED_BASELINE_NOT_DOMAIN_VERIFIED`, `domain_asset_gap=true`, `domain_verified=false` until its specialty Skills, Methods, tools, Golden/negative/regression cases and acceptance Evidence are actually present.

## Independent reviewer allocation

`aeris_runtime/reviewer_allocation.py` assigns reviewer **capability seats**, not external models. R0/R1 follow the risk policy. R2 gets one independent reviewer. R3/R4 get two independent reviewer seats and still require Human Chief Engineer approval.

Allocation is task-aware: standards/regulation, test automation/regression, reliability, requirements/traceability, red-team/risk, Evidence/reporting and measurement/quality hints influence deterministic reviewer ranking. When no task context is supplied, the allocator uses a deterministic primary-group fallback.

Reviewer safeguards:

- reviewer identity must differ from the primary role;
- fresh review context is required;
- reviewer cannot repair the same change and approve it;
- reviewer cannot write the primary Evidence;
- reviewer cannot impersonate Human release authority;
- no Claude or second model is launched by default.

## Truth boundary

Allocation is not review completion. A real review record/Evidence is still required where the R0-R4 policy requires independent review. The framework baseline does not upgrade the full `100_role_executable_domain_contracts` maturity item until specialty domain assets and acceptance coverage exist.
