"""Independent standards metadata/use/change-impact assertion assessment."""
from datetime import datetime
from .standard_metadata import validate,digest


def review(parameters,candidate):
    validate(parameters);p=parameters
    old=p['previous']['metadata'];meta=p['current']['metadata'];src=p['current']['source']
    def scope(record,region,domains):
        known=bool(record['regions']) and bool(record['domain_tags'])
        if not known:return 'UNKNOWN'
        region_match=any(r in (region,'GLOBAL') for r in record['regions'])
        domain_match=any(tag in record['domain_tags'] for tag in domains)
        return 'APPLICABLE' if region_match and domain_match else 'NOT_APPLICABLE'
    applicability=scope(meta,p['region'],p['domain_tags'])
    blockers=[]
    conditions=[('EDITION_UNKNOWN',meta['edition'] is None),
        ('DECLARED_STATUS_NOT_CURRENT',meta['status']!='CURRENT'),
        ('SUPERSEDED_EDITION',meta['superseded_by'] is not None),
        ('APPLICABILITY_UNKNOWN',applicability=='UNKNOWN'),
        ('NORMATIVE_CLASS_UNKNOWN',meta['normative_informative']=='UNKNOWN'),
        ('SOURCE_METADATA_INCOMPLETE',src['publisher'] is None or src['url'] is None)]
    blockers.extend(code for code,failed in conditions if failed)
    if src['retrieved_at'] is None:blockers.append('SOURCE_RETRIEVAL_UNKNOWN')
    else:
        age=datetime.fromisoformat(p['as_of'].replace('Z','+00:00'))-datetime.fromisoformat(src['retrieved_at'].replace('Z','+00:00'))
        if (age.days,age.seconds,age.microseconds)>(p['freshness_days'],0,0):blockers.append('SOURCE_STALE')
    expected_ids=[r['id'] for r in p['requirements'] if r['family']==meta['family'] and scope(meta,r['region'],r['domain_tags'])!='NOT_APPLICABLE']
    if any(identifier not in meta['requirement_ids'] for identifier in expected_ids):blockers.append('REQUIRED_REQUIREMENT_MAPPING_MISSING')
    license_blockers=[]
    if p['intended_use']=='NORMATIVE_USE':
        if meta['normative_informative']!='NORMATIVE':license_blockers.append('CLASSIFICATION_INCOMPATIBLE_WITH_NORMATIVE_USE')
        if meta['license_access'] not in ('PUBLIC_FULL_TEXT','USER_DECLARED_AUTHORIZED'):license_blockers.append('NORMATIVE_TEXT_ACCESS_UNCONFIRMED')
    semantic=[key for key in ('edition','status','superseded_by','regions','domain_tags','normative_informative','license_access','requirement_ids') if old[key]!=meta[key]]
    provenance=[key for key in ('record_id','publisher','url','retrieved_at','source_kind','content_sha256') if p['previous']['source'][key]!=src[key]]
    affected=set()
    if semantic:
        for record in (old,meta):
            for requirement in p['requirements']:
                if requirement['family']!=meta['family']:continue
                if requirement['id'] in record['requirement_ids'] or scope(record,requirement['region'],requirement['domain_tags'])!='NOT_APPLICABLE':
                    affected.add(requirement['id'])
    checks=[{'id':'DECLARED_SCOPE_APPLICABILITY','passed':applicability=='APPLICABLE','on_failure':'RESOLVE_SCOPE_OR_SELECT_APPLICABLE_FAMILY'},
            {'id':'METADATA_COMPLETENESS_AND_FRESHNESS','passed':not blockers,'on_failure':'OBTAIN_CURRENT_SOURCE_METADATA_WITH_PROVENANCE'},
            {'id':'DECLARED_ACCESS_FOR_INTENDED_USE','passed':not license_blockers,'on_failure':'CONFIRM_AUTHORIZED_ACCESS_WITH_HUMAN'},
            {'id':'SEMANTIC_CHANGE_REVIEW','passed':not semantic,'on_failure':'REVIEW_ALL_OLD_AND_NEW_SCOPE_REQUIREMENT_IMPACTS'}]
    expected={'family':meta['family'],'edition':meta['edition'],'as_of':p['as_of'],'applicability':applicability,
            'metadata_blockers':blockers,'license_blockers':license_blockers,'semantic_changes':semantic,
            'provenance_changes':provenance,'impacted_requirement_ids':sorted(affected),'checks':checks,
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
    same=isinstance(candidate,dict) and digest(candidate)==digest(expected)
    return {'decision':'BOUNDED_REVIEW_ACCEPT' if same else 'CHANGES_REQUIRED','expected':expected,
            'assertions_consistent':same,'human_approval':False,'role_l3_awarded':False,
            'review_scope':'Supplied metadata/access/change-impact consistency only; no normative/customer certification'}
