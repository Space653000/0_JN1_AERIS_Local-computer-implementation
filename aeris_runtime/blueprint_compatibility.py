"""Finalized Blueprint candidate contract; never infers running alignment."""
import hashlib
import json
from pathlib import Path

TARGET = '64576bdbe680170fc1ea27306d1a2ab494cac733'
TAG = 'v0.7.0-blueprint.1'
GOVERNANCE = '0.7.0-governance.4'

CONTRACT_HASHES = {
    'aeris.autopilot.json': 'f95f414dcf7d5c39435bd9ecf174c5f6f8044dae969a7f6a652d993187fd0de5',
    'aeris.review.json': 'b8bbb1e23b5f0bbd064106ada33265c5863b5a7dd1eef51b2233213e75231c71',
    'aeris.traceability.json': 'd4002e9d8666a8458f4f1dd3d63d0993b131868cdfce717c7d241dfbd2b22aa0',
}

# SHA consumers. Each key tuple resolves to the exact canonical Blueprint commit.
POINTERS = {
    'core.lock.json': ('baseline_sha',),
    'config/core_alignment.json': ('canonical_core', 'reviewed_sha'),
    'config/autopilot.json': ('canonical_core_sha',),
    'company/company.manifest.json': ('core_target', 'reviewed_sha'),
    'config/maturity.json': ('evidence_snapshot', 'canonical_core_reviewed_sha'),
    'config/review_gate.v1.json': ('source_blueprint_sha',),
    'config/blueprint_compatibility.json': ('target_commit',),
}

# Active governance consumers. Historical provenance is intentionally not scanned
# as an active pointer (e.g. superseded reviews and source-generation SHAs).
GOVERNANCE_POINTERS = {
    'config/blueprint_compatibility.json': ('governance_revision',),
    'config/core_alignment.json': ('review_alignment', 'architecture_version'),
    'config/autopilot.json': ('review_revision',),
    'config/review_gate.v1.json': ('architecture_version',),
}


def _load_json(root, relative):
    return json.loads((Path(root) / relative).read_text(encoding='utf-8-sig'))


def _get(value, keys):
    for key in keys:
        value = value[key]
    return value


def load_contracts(root):
    """Load byte-pinned public Core contract mirrors.

    CRLF -> LF is the sole normalization for Windows worktrees. CI separately
    compares these bytes to the immutable upstream commit, so changing the local
    mirror cannot make an incompatible schema authoritative.
    """
    documents = {}
    for name, expected in CONTRACT_HASHES.items():
        raw = (Path(root) / 'config/blueprint' / name).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('incompatible or tampered schema consumer source: BLOCKED')
        documents[name] = json.loads(raw)

    auto = documents['aeris.autopilot.json']
    review = documents['aeris.review.json']
    trace = documents['aeris.traceability.json']
    if auto.get('schema_version') != 3 or review.get('schema_version') != 3 or trace.get('schema_version') != 1:
        raise ValueError('unsupported schema consumer: BLOCKED')
    if (
        auto.get('review_revision') != GOVERNANCE
        or review.get('architecture_version') != GOVERNANCE
        or trace.get('architecture_version') != GOVERNANCE
    ):
        raise ValueError('finalized Blueprint governance revision mismatch: BLOCKED')
    if (
        auto['trigger'].get('interpretation') != 'PROJECT_IDENTIFICATION_ONLY'
        or auto['trigger'].get('requires_scoped_authorization') is not True
        or auto.get('truth_rule') != 'NO EVIDENCE = NOT DONE; admission before trigger; one bounded gate at a time'
        or review['human_authority'].get('reviewer_pass_is_release_authority') is not False
        or review['review_routing'].get('same_context_repair_approval') is not False
        or review.get('state') != 'REVIEW_PENDING'
        or trace['workstreams']['E'].get('status') != 'NOT_STARTED'
    ):
        raise ValueError('Blueprint semantic admission incompatible: BLOCKED')
    return documents


def _validate_active_semantics(root):
    compat = _load_json(root, 'config/blueprint_compatibility.json')
    if (
        compat.get('target_commit') != TARGET
        or compat.get('target_tag') != TAG
        or compat.get('governance_revision') != GOVERNANCE
        or compat.get('runtime_cutover_allowed') is not False
        or compat.get('E_acceptance_allowed') is not False
    ):
        raise ValueError('Gate-06 compatibility policy drift: REJECT')

    lock = _load_json(root, 'core.lock.json')
    if (
        lock.get('baseline_sha') != TARGET
        or lock.get('tag') != TAG
        or lock.get('canonical_roles', {}).get('core_commit') != TARGET
    ):
        raise ValueError('mixed Core role/tag pointer versions: REJECT')

    alignment = _load_json(root, 'config/core_alignment.json')
    if (
        alignment.get('canonical_core', {}).get('reviewed_sha') != TARGET
        or alignment.get('canonical_core', {}).get('tag') != TAG
        or alignment.get('review_alignment', {}).get('architecture_version') != GOVERNANCE
        or alignment.get('review_alignment', {}).get('implementation_authorized') is not False
    ):
        raise ValueError('mixed Core/governance alignment consumer: REJECT')

    autopilot = _load_json(root, 'config/autopilot.json')
    trigger = autopilot.get('trigger', {})
    admission = autopilot.get('admission_precondition', {})
    if (
        autopilot.get('canonical_core_sha') != TARGET
        or autopilot.get('review_revision') != GOVERNANCE
        or autopilot.get('truth_rule') != 'NO EVIDENCE = NOT DONE; admission before trigger; one bounded gate at a time'
        or trigger.get('interpretation') != 'PROJECT_IDENTIFICATION_ONLY'
        or trigger.get('requires_scoped_authorization') is not True
        or admission.get('state') != 'GATE06_RETRY_R1_IN_PROGRESS'
        or admission.get('blueprint_state') != 'REVIEW_PENDING'
        or admission.get('contract') != 'config/blueprint/aeris.review.json'
        or admission.get('traceability_contract') != 'config/blueprint/aeris.traceability.json'
        or admission.get('gate_adapter') != 'config/review_gate.v1.json'
        or admission.get('E_full_local_acceptance') != 'NOT_STARTED'
        or admission.get('requires_scoped_authorization') is not True
        or admission.get('drift_stops_construction') is not True
        or admission.get('runtime_enforcement_implemented') is not False
    ):
        raise ValueError('active Autopilot governance consumer drift: REJECT')

    company = _load_json(root, 'company/company.manifest.json')
    company_auto = company.get('autopilot', {})
    if (
        company.get('core_target', {}).get('reviewed_sha') != TARGET
        or company.get('core_target', {}).get('tag') != TAG
        or company_auto.get('interpretation') != 'PROJECT_IDENTIFICATION_ONLY'
        or company_auto.get('requires_scoped_authorization') is not True
        or 'HOLD_FOR_SOL_RED_TEAM' in str(company.get('review_hold', ''))
    ):
        raise ValueError('company manifest governance consumer drift: REJECT')

    gate = _load_json(root, 'config/review_gate.v1.json')
    if (
        gate.get('source_blueprint_sha') != TARGET
        or gate.get('architecture_version') != GOVERNANCE
        or gate.get('state') != 'GATE06_RETRY_R1_IN_PROGRESS'
        or gate.get('implementation_authorized') is not False
    ):
        raise ValueError('Gate-06 review adapter drift: REJECT')


def validate(root, consumers=None, runtime=None):
    # Caller labels are never proof of consumer compatibility.
    if consumers is not None:
        raise ValueError('caller-supplied compatibility assertion: BLOCKED')

    documents = load_contracts(root)
    rows = []
    for path, keys in POINTERS.items():
        try:
            current = _get(_load_json(root, path), keys)
        except (OSError, ValueError, KeyError, TypeError):
            current = 'UNKNOWN'
        rows.append({
            'consumer': path,
            'current': current,
            'target': TARGET,
            'state': 'COMPATIBLE' if current == TARGET else 'MIGRATION_REQUIRED',
        })
    if any(row['state'] != 'COMPATIBLE' for row in rows):
        raise ValueError('mixed Core pointer versions: REJECT')

    governance_rows = []
    for path, keys in GOVERNANCE_POINTERS.items():
        try:
            current = _get(_load_json(root, path), keys)
        except (OSError, ValueError, KeyError, TypeError):
            current = 'UNKNOWN'
        governance_rows.append({
            'consumer': path,
            'current': current,
            'target': GOVERNANCE,
            'state': 'COMPATIBLE' if current == GOVERNANCE else 'MIGRATION_REQUIRED',
        })
    if any(row['state'] != 'COMPATIBLE' for row in governance_rows):
        raise ValueError('mixed governance revision consumers: REJECT')

    _validate_active_semantics(root)

    packs = sorted((Path(root) / 'company/capabilities').glob('R*/capability.json'))
    expected_roles = {f'R{i:03d}' for i in range(1, 101)}
    if {path.parent.name for path in packs} != expected_roles:
        raise ValueError('incomplete canonical role pointer set: BLOCKED')
    for path in packs:
        role = json.loads(path.read_text(encoding='utf-8-sig'))
        if role.get('canonical_core_sha') != TARGET:
            raise ValueError(f'mixed Core Role Pack pointer versions: REJECT {path.parent.name}')
        # Provenance may intentionally remain at the generation SHA. It cannot
        # be mistaken for the active canonical pointer.
        if 'source_generation_core_sha' not in role:
            raise ValueError(f'Role Pack source-generation provenance missing: BLOCKED {path.parent.name}')

    if runtime and runtime.get('aligned') is True:
        if (
            runtime.get('core_sha') != TARGET
            or runtime.get('implementation_sha') != runtime.get('candidate_sha')
        ):
            raise ValueError('old runtime SHA cannot declare aligned')

    return {
        'pointers': rows,
        'governance': governance_rows,
        'parsed_contract_schemas': {key: value['schema_version'] for key, value in documents.items()},
        'runtime': runtime or {'state': 'UNKNOWN'},
        'claim_scope': 'PIN_SCHEMA_AND_ACTIVE_GOVERNANCE_ADAPTER_ONLY_NOT_SYSTEM_ACCEPTANCE',
        'four_way_aligned': False,
        'runtime_cutover': False,
    }
