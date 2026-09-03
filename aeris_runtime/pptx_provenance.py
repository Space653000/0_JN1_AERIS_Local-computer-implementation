"""Read-only provenance verification for the locally reviewed PPTX capability."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PureWindowsPath
from typing import Any

from .config import ROOT

PROVENANCE = ROOT / "config" / "pptx_beautify_lock.provenance.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _relative(value: str, *, private: bool = False) -> str:
    if not isinstance(value,str) or not value: raise ValueError('relative artifact path required')
    path=PureWindowsPath(value)
    if path.drive or path.root or '..' in path.parts or ':' in value:
        raise ValueError('unsafe artifact path')
    normalized='/'.join(path.parts)
    if not normalized: raise ValueError('artifact filename required')
    if private and not normalized.startswith('.aeris/'):
        raise ValueError('review artifacts must remain local-only under .aeris')
    return normalized


def portable_contract(spec: dict) -> dict:
    """Metadata validation only. Does not attest that artifacts exist or ran."""
    errors=[]
    try:
        if spec['schema_version']!=1: raise ValueError('unsupported provenance schema')
        if spec['upstream_repository']!='https://github.com/Space653000/pptx-beautify-lock-Skill':
            raise ValueError('unexpected upstream repository')
        if not re.fullmatch('[0-9a-f]{40}',spec['upstream_commit']): raise ValueError('pinned upstream commit required')
        _relative(spec['source_root'],private=True)
        if not isinstance(spec['source_files'],dict) or not spec['source_files']: raise ValueError('source hashes required')
        for rel,expected in spec['source_files'].items():
            _relative(rel)
            if not re.fullmatch('[0-9A-Fa-f]{64}',expected): raise ValueError('invalid source SHA-256')
        executable=spec['executable']
        _relative(executable['path'],private=True)
        if not re.fullmatch('[0-9A-Fa-f]{64}',executable['sha256']): raise ValueError('invalid executable SHA-256')
        if type(executable['bytes']) is not int or executable['bytes']<=0: raise ValueError('invalid executable size')
        if executable['authenticode']!='NOT_SIGNED': raise ValueError('signed trust is not established by this contract')
        if spec['acceptance']!='PACKAGE_PROVENANCE_VERIFIED_NOT_DECK_PRODUCTION_ACCEPTED':
            raise ValueError('production acceptance cannot be granted by package metadata')
    except (KeyError,TypeError,ValueError) as exc: errors.append(str(exc))
    return {'kind':'PORTABLE_PROVENANCE_CONTRACT','state':'INVALID' if errors else 'VALID',
            'errors':errors,'artifact_presence_verified':False,'local_only_policy':'.aeris',
            'assurance':'metadata consistency, not signed upstream authenticity or production acceptance'}


def verify(_: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        spec=json.loads(PROVENANCE.read_text(encoding='utf-8-sig'))
        contract=portable_contract(spec)
    except (OSError,ValueError) as exc:
        spec={}; contract={'kind':'PORTABLE_PROVENANCE_CONTRACT','state':'INVALID','errors':[str(exc)]}
    result={'skill_id':'pptx-beautify-lock-local','result':'FAIL','provenance_valid':False,
            'portable_provenance_contract':contract,'checks':[],'authenticode':'NOT_SIGNED',
            'trusted_signed_binary':False,'production_acceptance':'NOT_RUN_NO_INPUT_PPTX',
            'capability_maturity':'INVALID_PROVENANCE_CONTRACT',
            'truth':'Unsigned local package hashes are not signed trust; no input PPTX means no deck acceptance.'}
    if contract['state']!='VALID': return result
    entries=[('SOURCE',_relative(spec['source_root'])+'/'+_relative(rel),expected,None)
             for rel,expected in spec['source_files'].items()]
    exe=spec['executable']
    entries.append(('EXECUTABLE',_relative(exe['path']),exe['sha256'],exe['bytes']))
    checks=result['checks']
    for kind,relative,expected,size in entries:
        path=(ROOT/relative).resolve()
        if not path.is_relative_to((ROOT/'.aeris').resolve()):
            checks.append({'kind':kind,'path':relative,'state':'UNSAFE_PATH','valid':False})
            continue
        exists=path.exists()
        actual=_sha256(path) if path.is_file() else None
        actual_size=path.stat().st_size if path.is_file() else None
        valid=actual==expected.upper() and (size is None or size==actual_size)
        state='VERIFIED' if valid else 'TAMPERED_OR_INVALID' if exists else 'LOCAL_ARTIFACT_NOT_PRESENT'
        checks.append({'kind':kind,'path':relative,'expected_sha256':expected,'actual_sha256':actual,
                       'bytes':actual_size,'valid':valid,'state':state})
    valid=all(c['valid'] for c in checks)
    state=('VERIFIED' if valid else 'FAILED' if any(c['state'] in {'TAMPERED_OR_INVALID','UNSAFE_PATH'} for c in checks)
           else 'LOCAL_ARTIFACT_NOT_PRESENT')
    result.update({'result':'PASS' if valid else 'FAIL' if state=='FAILED' else state,
                   'provenance_valid':valid,'local_artifact_verification':{'kind':'LOCAL_ARTIFACT_VERIFICATION','state':state},
                   'capability_maturity':spec['acceptance'] if valid else state})
    return result
