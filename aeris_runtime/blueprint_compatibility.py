"""Finalized Blueprint candidate contract; never infers running alignment."""
import json
import hashlib
from pathlib import Path

TARGET = '64576bdbe680170fc1ea27306d1a2ab494cac733'
TAG = 'v0.7.0-blueprint.1'
CONTRACT_HASHES = {
    'aeris.autopilot.json': 'f95f414dcf7d5c39435bd9ecf174c5f6f8044dae969a7f6a652d993187fd0de5',
    'aeris.review.json': 'b8bbb1e23b5f0bbd064106ada33265c5863b5a7dd1eef51b2233213e75231c71',
    'aeris.traceability.json': 'd4002e9d8666a8458f4f1dd3d63d0993b131868cdfce717c7d241dfbd2b22aa0',
}
POINTERS = {
    'core.lock.json': ('baseline_sha',),
    'config/core_alignment.json': ('canonical_core','reviewed_sha'),
    'config/autopilot.json': ('canonical_core_sha',),
    'company/company.manifest.json': ('core_target','reviewed_sha'),
    'config/maturity.json': ('evidence_snapshot','canonical_core_reviewed_sha'),
    'config/review_gate.v1.json': ('source_blueprint_sha',),
}


def load_contracts(root):
    """Pinned byte-exact public source mirrors, not a second editable SSOT.

    Windows checkout newline conversion is the sole normalization. CI must also
    compare these bytes to the immutable upstream commit, independently of pins.
    """
    documents = {}
    for name, expected in CONTRACT_HASHES.items():
        raw = (Path(root)/'config/blueprint'/name).read_bytes().replace(b'\r\n',b'\n')
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('incompatible or tampered schema consumer source: BLOCKED')
        documents[name] = json.loads(raw)
    auto, review, trace = (documents[n] for n in CONTRACT_HASHES)
    if auto['schema_version'] != 3 or review['schema_version'] != 3 or trace['schema_version'] != 1:
        raise ValueError('unsupported schema consumer: BLOCKED')
    if (auto['trigger']['interpretation'] != 'PROJECT_IDENTIFICATION_ONLY'
            or auto['trigger']['requires_scoped_authorization'] is not True
            or review['human_authority']['reviewer_pass_is_release_authority'] is not False
            or review['review_routing']['same_context_repair_approval'] is not False
            or trace['workstreams']['E']['status'] != 'NOT_STARTED'):
        raise ValueError('Blueprint semantic admission incompatible: BLOCKED')
    return documents


def validate(root, consumers=None, runtime=None):
    # Caller labels are never proof of consumer compatibility.
    if consumers is not None:
        raise ValueError('caller-supplied compatibility assertion: BLOCKED')
    documents = load_contracts(root)
    rows = []
    for path, keys in POINTERS.items():
        try:
            value = json.loads((Path(root)/path).read_text(encoding='utf-8-sig'))
            for key in keys: value = value[key]
        except (OSError, ValueError, KeyError, TypeError): value = 'UNKNOWN'
        rows.append({'consumer':path,'current':value,'target':TARGET,
                     'state':'COMPATIBLE' if value == TARGET else 'MIGRATION_REQUIRED'})
    if any(row['state'] != 'COMPATIBLE' for row in rows):
        raise ValueError('mixed Core pointer versions: REJECT')
    lock = json.loads((Path(root)/'core.lock.json').read_text(encoding='utf-8-sig'))
    if lock.get('canonical_roles',{}).get('core_commit') != TARGET or lock.get('tag') != TAG:
        raise ValueError('mixed Core role/tag pointer versions: REJECT')
    packs = sorted((Path(root)/'company/capabilities').glob('R*/capability.json'))
    expected_roles = {f'R{i:03d}' for i in range(1,101)}
    if {p.parent.name for p in packs} != expected_roles:
        raise ValueError('incomplete canonical role pointer set: BLOCKED')
    for path in packs:
        if json.loads(path.read_text(encoding='utf-8-sig')).get('canonical_core_sha') != TARGET:
            raise ValueError(f'mixed Core Role Pack pointer versions: REJECT {path.parent.name}')
    if runtime and runtime.get('aligned') is True:
        if runtime.get('core_sha') != TARGET or runtime.get('implementation_sha') != runtime.get('candidate_sha'):
            raise ValueError('old runtime SHA cannot declare aligned')
    return {'pointers':rows,'parsed_contract_schemas':{k:v['schema_version'] for k,v in documents.items()},
            'runtime':runtime or {'state':'UNKNOWN'}, 'claim_scope':'PIN_AND_SCHEMA_ADAPTER_ONLY_NOT_SYSTEM_ACCEPTANCE',
            'four_way_aligned':False,'runtime_cutover':False}
