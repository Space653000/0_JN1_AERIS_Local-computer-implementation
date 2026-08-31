# Portable Company Architecture

## 三層真值

```text
READ-ONLY NORTH STAR
0_JN1_AERIS/main
        ↓
PORTABLE COMPANY IMAGE
this repository
        ↓
MACHINE INSTANCE
local state / models / private data / evidence
```

第二層必須是可版本化、可測試、可搬遷的完整公司資產；第三層則包含不可放 Git 的機器狀態與私有資料。

## Planes

1. Company Plane — Constitution / Governance / Organization / Business
2. Knowledge Plane — Skills / Methods / Standards / Memory / Knowledge Graph
3. Control Plane — Orchestrator / Requirement Parser / Role Router / Workflow Engine
4. Execution Plane — Model Router / Python / MATLAB / CAE / Lab / Firmware adapters
5. Trust Plane — Evidence / Verification / Approval / Reproduction
6. Experience Plane — Dashboard / Workspace / Services
7. Operations Plane — Audit / Health / backup / migration / observability

## Portability boundary

Tracked in Git:

- code, configs, schemas, docs, role/skill/method definitions;
- installer / health / package / migration scripts;
- non-secret sample configs;
- deterministic tests and lightweight golden fixtures.

Not tracked in Git:

- model weights;
- secrets;
- customer/private data;
- proprietary tools/licenses;
- large raw measurement/simulation outputs.

These are represented by manifests and optional offline asset packs.
