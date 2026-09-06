"""AERIS local standards registry.

Registry entries are useful for discovery even when not live-verified, but formal-use
lookup fails closed unless the exact edition/status has been explicitly verified.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .config import ROOT

REGISTRY_PATH = ROOT / "standards" / "registry.v1.json"


def load_registry() -> dict[str, Any]:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1 or not isinstance(data.get("standards"), list):
        raise ValueError("invalid standards registry")
    return data


def list_standards() -> list[dict[str, Any]]:
    return list(load_registry()["standards"])


def search_standards(query: str) -> list[dict[str, Any]]:
    q = query.strip().lower()
    if not q:
        return list_standards()
    return [
        item for item in list_standards()
        if q in str(item.get("standard_id", "")).lower()
        or q in str(item.get("title", "")).lower()
        or q in " ".join(str(x) for x in item.get("keywords", [])).lower()
    ]


def require_formal_use(standard_id: str, *, context: dict | None = None) -> dict[str, Any]:
    matches = [s for s in list_standards() if str(s.get("standard_id", "")).lower() == standard_id.strip().lower()]
    if not matches:
        raise KeyError(standard_id)
    item = matches[0]
    if item.get("verification_state") != "LIVE_VERIFIED" or not item.get("verified_at_utc") or not item.get("source_url"):
        raise RuntimeError(f"STANDARD_NOT_LIVE_VERIFIED_FOR_FORMAL_USE: {standard_id}")
    if context is None:
        raise RuntimeError(f'STANDARD_FORMAL_SCOPE_REQUIRED: {standard_id}')
    assessment=assess_applicability(item,{**context,'formal_use':True})
    if assessment['state']!='ELIGIBLE_FOR_DOMAIN_REVIEW':
        raise RuntimeError(f"STANDARD_FORMAL_USE_BLOCKED: {standard_id}: {assessment['state']}: {assessment['blockers']}")
    return {**item,'metadata_assessment':assessment,'formal_conformance_verified':False}


def assess_applicability(record: dict, context: dict) -> dict:
    """Bounded metadata decision support, never a conformance certificate.

Explicit applicability scopes are required; discovery keywords cannot silently
establish legal/product applicability. Licensing gates do not block free
engineering calculations, but they do block formal normative-text assertions.
"""
    region=context.get('region'); domains=context.get('domain_tags')
    if not isinstance(region,str) or not region or not isinstance(domains,list) or not domains:
        raise ValueError('region and explicit domain tags required')
    if any(not isinstance(d,str) or not d for d in domains): raise ValueError('nonempty domain tags required')
    formal=context.get('formal_use',False)
    if type(formal) is not bool: raise ValueError('formal_use must be boolean')
    blockers=[]; scope=record.get('applicability',{})
    family=record.get('family',record.get('standard_id'))
    if not family: blockers.append('STANDARD_FAMILY_UNKNOWN')
    if not record.get('edition'): blockers.append('EDITION_UNKNOWN')
    if record.get('status') not in {'CURRENT','ACTIVE'}: blockers.append('STATUS_NOT_CURRENT')
    if record.get('superseded_by'): blockers.append('SUPERSEDED_EDITION')
    domain_scope=scope.get('domain_tags',[]); regions=scope.get('regions',[])
    if not domain_scope or not regions: blockers.append('APPLICABILITY_SCOPE_UNKNOWN')
    out_of_scope=bool(domain_scope and not set(domains)&set(domain_scope)) or bool(regions and region not in regions and 'GLOBAL' not in regions)
    if record.get('normative_informative') not in {'NORMATIVE','INFORMATIVE'}: blockers.append('NORMATIVE_CLASS_UNKNOWN')
    source=urlsplit(record.get('source_url') or '')
    if source.scheme!='https' or not source.hostname or source.username or source.password:
        blockers.append('SOURCE_PROVENANCE_UNKNOWN')
    if not re.fullmatch('[0-9a-fA-F]{64}',record.get('source_sha256','')): blockers.append('SOURCE_HASH_UNKNOWN')
    try:
        verified=datetime.fromisoformat(str(record.get('verified_at_utc','')).replace('Z','+00:00'))
        if verified.tzinfo is None: raise ValueError('timezone required')
        age=(datetime.now(timezone.utc)-verified).total_seconds()
        if age<0 or age>180*86400: blockers.append('METADATA_VERIFICATION_STALE')
    except (ValueError,TypeError): blockers.append('METADATA_VERIFICATION_DATE_UNKNOWN')
    if record.get('verification_state')!='LIVE_VERIFIED': blockers.append('METADATA_NOT_LIVE_VERIFIED')
    access=record.get('license_access','METADATA_ONLY')
    if formal and record.get('normative_informative')!='INFORMATIVE' and access not in {'PUBLIC_FULL_TEXT','AUTHORIZED_FULL_TEXT'}:
        blockers.append('NORMATIVE_TEXT_ACCESS_NOT_AUTHORIZED')
    state=('NOT_APPLICABLE' if out_of_scope else 'BLOCKED_METADATA' if blockers else 'ELIGIBLE_FOR_DOMAIN_REVIEW')
    return {'family':family,'edition':record.get('edition'),'region':region,'state':state,
            'blockers':blockers,'requirement_links':record.get('requirement_links',[]),
            'source_ref':record.get('source_url'),'source_sha256':record.get('source_sha256'),
            'normative_informative':record.get('normative_informative','UNKNOWN'),
            'license_access':access,'formal_conformance_verified':False,'free_baseline_execution_allowed':True,
            'truth':'Metadata applicability support only; Human/domain review, licensed text where required, and actual tests remain separate.'}


def change_impact(previous: dict, current: dict, requirement_links: list[dict]) -> dict:
    """Identify exactly which traceability links need re-review after metadata drift."""
    family=previous.get('family',previous.get('standard_id'))
    if not family or family!=current.get('family',current.get('standard_id')):
        raise ValueError('change comparison requires the same standards family')
    fields=('edition','status','superseded_by','applicability','normative_informative',
            'source_url','source_sha256','license_access','verification_state')
    changes=[{'field':field,'previous':previous.get(field),'current':current.get(field)}
             for field in fields if previous.get(field)!=current.get(field)]
    affected=[]
    for link in requirement_links:
        if not link.get('requirement_id') or not link.get('standard_family'):
            raise ValueError('explicit requirement ID and standards family required')
        if link['standard_family']==family and changes:
            affected.append({'requirement_id':link['requirement_id'],'test_id':link.get('test_id'),
                             'disposition':'REVIEW_REQUIRED','reason_fields':[c['field'] for c in changes]})
    return {'family':family,'changes':changes,'affected_requirements':affected,
            'state':'REVIEW_REQUIRED' if changes else 'NO_METADATA_CHANGE',
            'automatic_requirement_rewrite':False,'formal_conformance_verified':False}
