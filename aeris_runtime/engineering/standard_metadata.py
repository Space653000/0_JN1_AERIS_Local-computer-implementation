"""Deterministic supplied metadata reasoning; never a live standards verdict."""
import hashlib
import json
from datetime import datetime,timedelta
from urllib.parse import urlsplit

SEMANTIC_FIELDS=('edition','status','superseded_by','regions','domain_tags','normative_informative','license_access','requirement_ids')
SOURCE_FIELDS=('record_id','publisher','url','retrieved_at','source_kind','content_sha256')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def from_registry(entry,requirement_ids):
    """Project actual discovery metadata without inventing retrieval or edition.

    The hash identifies this declared metadata projection, not a fetched source
    document. Caller-supplied requirement mappings stay explicit and unverified.
    """
    if not isinstance(entry,dict):raise ValueError('registry entry required')
    scope=entry.get('applicability') or {}
    meta={'family':entry.get('family',entry.get('standard_id')),'edition':entry.get('edition'),
          'status':entry.get('status') if entry.get('status') in ('CURRENT','SUPERSEDED') else 'UNKNOWN',
          'superseded_by':entry.get('superseded_by'),'regions':scope.get('regions',[]),
          'domain_tags':scope.get('domain_tags',[]),'normative_informative':entry.get('normative_informative','UNKNOWN'),
          'license_access':entry.get('license_access','UNKNOWN'),'requirement_ids':list(requirement_ids)}
    return {'metadata':meta,'source':{'record_id':'REGISTRY-'+digest(entry)[:24],
            'publisher':entry.get('publisher'),'url':entry.get('source_url'),'retrieved_at':entry.get('retrieved_at_utc'),
            'source_kind':'REGISTRY_UNVERIFIED','content_sha256':digest(meta)}}


def _object(value,keys):
    if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError('exact metadata contract required')


def _text(value,unknown=False):
    if value is None and unknown:return
    if not isinstance(value,str) or not value.strip() or len(value)>1000:raise ValueError('bounded metadata text required')


def _list(value):
    if not isinstance(value,list) or len(value)>256:raise ValueError('bounded metadata identity list required')
    for entry in value:_text(entry)
    if len(value)!=len(set(value)):raise ValueError('duplicate metadata identity')


def _time(value):
    _text(value)
    try:parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:raise ValueError('ISO timestamp required') from exc
    if parsed.tzinfo is None:raise ValueError('timezone required')
    return parsed


def validate(p):
    _object(p,('as_of','freshness_days','intended_use','region','domain_tags','requirements','previous','current'))
    at=_time(p['as_of']);_text(p['region']);_list(p['domain_tags'])
    if not p['domain_tags']:raise ValueError('explicit intended domain required')
    if type(p['freshness_days']) is not int or not 1<=p['freshness_days']<=365:raise ValueError('bounded pinned freshness policy required')
    if p['intended_use'] not in ('METADATA_ONLY','NORMATIVE_USE'):raise ValueError('explicit use scope required')
    if not isinstance(p['requirements'],list) or not 1<=len(p['requirements'])<=256:raise ValueError('independent requirements required')
    ids=[]
    for requirement in p['requirements']:
        _object(requirement,('id','family','region','domain_tags'))
        for key in ('id','family','region'):_text(requirement[key])
        _list(requirement['domain_tags'])
        if not requirement['domain_tags']:raise ValueError('requirement domain required')
        ids.append(requirement['id'])
    if len(ids)!=len(set(ids)):raise ValueError('duplicate requirement identity')
    for record in (p['previous'],p['current']):
        _object(record,('metadata','source'));meta=record['metadata'];source=record['source']
        _object(meta,('family',*SEMANTIC_FIELDS));_text(meta['family']);_text(meta['edition'],True);_text(meta['superseded_by'],True)
        for key in ('regions','domain_tags','requirement_ids'):_list(meta[key])
        if set(meta['requirement_ids'])-set(ids):raise ValueError('dangling metadata requirement mapping')
        if any(req['id'] in meta['requirement_ids'] and req['family']!=meta['family'] for req in p['requirements']):
            raise ValueError('requirement mapping belongs to another family')
        if meta['status'] not in ('CURRENT','SUPERSEDED','UNKNOWN'):raise ValueError('unknown declared status')
        if meta['normative_informative'] not in ('NORMATIVE','INFORMATIVE','UNKNOWN'):raise ValueError('unknown classification')
        if meta['license_access'] not in ('METADATA_ONLY','PUBLIC_FULL_TEXT','USER_DECLARED_AUTHORIZED','UNKNOWN'):raise ValueError('unknown access declaration')
        _object(source,SOURCE_FIELDS);_text(source['record_id']);_text(source['publisher'],True);_text(source['url'],True)
        if source['source_kind'] not in ('SYNTHETIC','SUPPLIED_UNVERIFIED','REGISTRY_UNVERIFIED'):raise ValueError('cannot assert verified source')
        if source['content_sha256']!=digest(meta):raise ValueError('metadata content identity mismatch')
        if source['retrieved_at'] is not None and _time(source['retrieved_at'])>at:raise ValueError('future source retrieval')
        if source['url'] is not None:
            url=urlsplit(source['url'])
            if url.scheme!='https' or not url.hostname or url.username or url.password:raise ValueError('credential-free HTTPS metadata reference required')
        if source['source_kind']=='SYNTHETIC':
            if not meta['family'].startswith('SYNTHETIC-') or urlsplit(source['url'] or '').hostname!='example.invalid':
                raise ValueError('synthetic fixture must use fictitious family and reserved source URL')
    if p['previous']['metadata']['family']!=p['current']['metadata']['family']:raise ValueError('comparison requires one family')
    return at


def _scope(meta,region,domains):
    if not meta['regions'] or not meta['domain_tags']:return 'UNKNOWN'
    return 'APPLICABLE' if (region in meta['regions'] or 'GLOBAL' in meta['regions']) and set(domains)&set(meta['domain_tags']) else 'NOT_APPLICABLE'


def analyze(parameters):
    at=validate(parameters);p=parameters
    previous=p['previous']['metadata'];current=p['current']['metadata'];source=p['current']['source']
    applicability=_scope(current,p['region'],p['domain_tags'])
    blockers=[]
    if current['edition'] is None:blockers.append('EDITION_UNKNOWN')
    if current['status']!='CURRENT':blockers.append('DECLARED_STATUS_NOT_CURRENT')
    if current['superseded_by'] is not None:blockers.append('SUPERSEDED_EDITION')
    if applicability=='UNKNOWN':blockers.append('APPLICABILITY_UNKNOWN')
    if current['normative_informative']=='UNKNOWN':blockers.append('NORMATIVE_CLASS_UNKNOWN')
    if source['publisher'] is None or source['url'] is None:blockers.append('SOURCE_METADATA_INCOMPLETE')
    if source['retrieved_at'] is None:blockers.append('SOURCE_RETRIEVAL_UNKNOWN')
    elif at-_time(source['retrieved_at'])>timedelta(days=p['freshness_days']):blockers.append('SOURCE_STALE')
    required={req['id'] for req in p['requirements'] if req['family']==current['family'] and _scope(current,req['region'],req['domain_tags'])!='NOT_APPLICABLE'}
    if required-set(current['requirement_ids']):blockers.append('REQUIRED_REQUIREMENT_MAPPING_MISSING')
    license_blockers=[]
    if p['intended_use']=='NORMATIVE_USE':
        if current['normative_informative']!='NORMATIVE':
            license_blockers.append('CLASSIFICATION_INCOMPATIBLE_WITH_NORMATIVE_USE')
        if current['license_access'] not in ('PUBLIC_FULL_TEXT','USER_DECLARED_AUTHORIZED'):
            license_blockers.append('NORMATIVE_TEXT_ACCESS_UNCONFIRMED')
    changes=[field for field in SEMANTIC_FIELDS if previous[field]!=current[field]]
    provenance=[field for field in SOURCE_FIELDS if p['previous']['source'][field]!=source[field]]
    impacted=[]
    if changes:
        for req in p['requirements']:
            if req['family']!=current['family']:continue
            old=_scope(previous,req['region'],req['domain_tags']);new=_scope(current,req['region'],req['domain_tags'])
            if req['id'] in set(previous['requirement_ids'])|set(current['requirement_ids']) or old!='NOT_APPLICABLE' or new!='NOT_APPLICABLE':
                impacted.append(req['id'])
    checks=[{'id':'DECLARED_SCOPE_APPLICABILITY','passed':applicability=='APPLICABLE','on_failure':'RESOLVE_SCOPE_OR_SELECT_APPLICABLE_FAMILY'},
            {'id':'METADATA_COMPLETENESS_AND_FRESHNESS','passed':not blockers,'on_failure':'OBTAIN_CURRENT_SOURCE_METADATA_WITH_PROVENANCE'},
            {'id':'DECLARED_ACCESS_FOR_INTENDED_USE','passed':not license_blockers,'on_failure':'CONFIRM_AUTHORIZED_ACCESS_WITH_HUMAN'},
            {'id':'SEMANTIC_CHANGE_REVIEW','passed':not changes,'on_failure':'REVIEW_ALL_OLD_AND_NEW_SCOPE_REQUIREMENT_IMPACTS'}]
    return {'family':current['family'],'edition':current['edition'],'as_of':p['as_of'],'applicability':applicability,
            'metadata_blockers':blockers,'license_blockers':license_blockers,'semantic_changes':changes,
            'provenance_changes':provenance,'impacted_requirement_ids':sorted(impacted),'checks':checks,
            'required_revisions':[c['on_failure'] for c in checks if not c['passed']],
            'disposition':'BOUNDED_BASELINE_ACCEPT' if all(c['passed'] for c in checks) else 'DESIGN_REVISION_REQUIRED',
            'live_verified':False,'source_authenticity_verified':False,'formal_conformance_verified':False,
            'physical_measurement_verified':False,'customer_approval':False,'free_baseline_execution_allowed':True,
            'counter_hypotheses':['Regional adoption or scope difference rather than contradictory standard',
                'Retrieval refresh rather than semantic edition change'],
            'next_discriminating_experiment':'VERIFY_EXACT_EDITION_SCOPE_AND_REQUIREMENT_IMPACT_WITH_AUTHORIZED_SOURCE',
            'model_assumptions':['Supplied metadata declarations are not live-verified facts',
                'Freshness uses pinned as-of time; content identity is not authenticity',
                'Previous/current scope union preserves requirements removed from current scope'],
            'unresolved':['Actual authoritative source verification','Normative access rights and qualified Human/customer review']}


def validate_revision(initial,revised):
    """Only a hypothetical newer retrieval; never a new edition or policy."""
    validate(initial);validate(revised)
    for key in initial:
        if key!='current' and digest(initial[key])!=digest(revised[key]):
            raise ValueError('refresh changed context, policy or previous snapshot')
    old=initial['current'];new=revised['current']
    if digest(old['metadata'])!=digest(new['metadata']):raise ValueError('refresh cannot change semantic content')
    for key in SOURCE_FIELDS:
        if key not in ('record_id','retrieved_at') and old['source'][key]!=new['source'][key]:
            raise ValueError('refresh changed source publisher/URL/type/content identity')
    existing_ids={old['source']['record_id'],initial['previous']['source']['record_id']}
    if new['source']['source_kind']!='SYNTHETIC' or new['source']['record_id'] in existing_ids:
        raise ValueError('new explicitly hypothetical source record required')
    if old['source']['retrieved_at'] is None or new['source']['retrieved_at'] is None or _time(new['source']['retrieved_at'])<=_time(old['source']['retrieved_at']):
        raise ValueError('strictly newer bounded hypothetical retrieval required')
    return True
