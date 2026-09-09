"""Pinned extraction of Core identities; no runtime dependency on private cache.

Offline consistency is not authenticity against coordinated edits of registry and
pin. CI separately compares the source at the locked canonical Git commit.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPOSITORY='https://github.com/Space653000/0_JN1_AERIS.git'
EXTRACTION='AERIS_ROLE_GROUPS_ORDERED_V1'


def semantic_digest(groups):
    # Group order is identity-bearing: sorting keys would silently reassign IDs.
    raw=json.dumps(list(groups.items()),ensure_ascii=False,separators=(',',':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def validate_source(data: bytes, pin: dict, groups: dict):
    # Git working trees may translate LF to CRLF; this is the declared only
    # source normalization. Pin hashes canonical LF source bytes, not JSON.
    normalized=data.replace(b'\r\n',b'\n')
    if hashlib.sha256(normalized).hexdigest()!=pin['source_sha256_lf']:
        raise ValueError('Core source digest drift')
    match=re.search(r'window\.AERIS_ROLE_GROUPS\s*=\s*(\{.*?\});',normalized.decode('utf-8-sig'),re.S)
    if not match or semantic_digest(json.loads(match[1]))!=semantic_digest(groups):
        raise ValueError('role registry drift from read-only Core')


def load(root: Path):
    registry=json.loads((root/'company/organization/roles.v1.json').read_text(encoding='utf-8-sig'))
    lock=json.loads((root/'core.lock.json').read_text(encoding='utf-8-sig'))
    pin=lock.get('canonical_roles',{})
    if (lock.get('core_repository')!=REPOSITORY or pin.get('core_commit')!=lock.get('baseline_sha')
            or pin.get('extraction')!=EXTRACTION or pin.get('source_path')!='aeris-data.js'
            or not re.fullmatch('[0-9a-f]{64}',pin.get('source_sha256_lf',''))):
        raise ValueError('invalid canonical role pin')
    groups=registry['groups']
    if registry.get('source_core_repo')!='Space653000/0_JN1_AERIS' or registry.get('source_policy')!='read_only':
        raise ValueError('role registry authority drift')
    if semantic_digest(groups)!=pin.get('ordered_groups_sha256'):
        raise ValueError('canonical role semantic digest drift')
    cache=root/'.aeris/core-reference/aeris-data.js'
    if cache.exists(): validate_source(cache.read_bytes(),pin,groups)
    return groups
