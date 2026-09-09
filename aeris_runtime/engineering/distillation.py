"""Deterministic source-linked Memory aggregation; never Evidence or expertise."""
from collections import Counter, defaultdict

from .catalog import digest

VERSION='source-event-distillation-v1'
DERIVED_KINDS={'RETROSPECTIVE','INSIGHT','KNOWLEDGE_DISTILLATION'}
REJECTED={'REJECT','REJECTED','FAIL','FAILED','BLOCKED','REVIEW_BLOCKED','DISAGREE'}


def derive(project,events):
    sources=[e for e in events if e['kind'] not in DERIVED_KINDS]
    hashes=[e['event_hash'] for e in sources]
    result={'project':project,'state':'DERIVED' if sources else 'NO_SOURCE_EVENTS',
            'distillation_version':VERSION,'source_event_hashes':hashes,
            'source_set_sha256':digest({'version':VERSION,'hashes':hashes}),
            'observed_events':len(sources),'memory_is_evidence':False,
            'method':'deterministic source event aggregation; reported causes are observations, not proven causal inference'}
    clusters=defaultdict(list); daily=defaultdict(list)
    observations=defaultdict(list)
    event_groups=defaultdict(list)
    failures=[]
    for event in sources:
        payload=event['payload']; kind=event['kind']; ref=event['event_hash']
        daily[event['created_at'][:10]].append(event)
        event_groups[kind].append({'source_event_hashes':[ref],'value':payload})
        decision=str(payload.get('decision',payload.get('review',{}).get('decision','') if isinstance(payload.get('review'),dict) else '')).upper()
        is_failure=kind=='FAILURE_LIBRARY' or payload.get('passed') is False or decision in REJECTED
        if is_failure:
            failures.append(event)
            failure=payload.get('failure_mode') or payload.get('error') or decision or 'UNCLASSIFIED_RECORDED_FAILURE'
            clusters[str(failure)].append(event)
        for source_key,target_key in (
                ('root_cause','root_cause_observations'),('lesson','lessons'),
                ('unresolved','unresolved_items'),('next_discriminating_experiment','next_discriminating_experiments'),
                ('discriminating_test','next_discriminating_experiments')):
            value=payload.get(source_key)
            if value not in (None,'',[],{}):
                observations[target_key].append({'value':value,'source_event_hashes':[ref],
                                                 'classification':'SOURCE_RECORDED_NOT_INDEPENDENTLY_PROVEN'})
    result.update({'failure_count':len(failures),
        'failure_clusters':[{'failure_mode':key,'count':len(items),
                             'source_event_hashes':[e['event_hash'] for e in items]} for key,items in sorted(clusters.items())],
        'project_summary':{'kind_counts':dict(sorted(Counter(e['kind'] for e in sources).items())),
                           'source_event_hashes':hashes},
        'daily_summaries':[{'date_utc':day,'events':len(items),'kind_counts':dict(Counter(e['kind'] for e in items)),
                            'source_event_hashes':[e['event_hash'] for e in items]} for day,items in sorted(daily.items())],
        'experiment_summaries':event_groups['EXPERIMENT_MEMORY'],
        'decision_summaries':event_groups['DECISION_MEMORY'],
        'cross_role_reviews':event_groups['CROSS_ROLE_REVIEW'],
        'disagreements':[e for e in event_groups['CONSENSUS_DISAGREEMENT']
                         if str(e['value'].get('decision','')).upper() in REJECTED or e['value'].get('unresolved')],
        'skill_usage':event_groups['SKILL_USAGE'],'regression_results':event_groups['GOLDEN_REGRESSION']})
    for key in ('root_cause_observations','lessons','unresolved_items','next_discriminating_experiments'):
        result[key]=observations[key]
    # An actual repeated failure observation is an insight candidate, with exact
    # provenance. No arbitrary failure becomes a fabricated root cause or lesson.
    result['insights']=[{'observation':f"Repeated recorded failure: {c['failure_mode']}",
                         'occurrences':c['count'],'source_event_hashes':c['source_event_hashes']}
                        for c in result['failure_clusters'] if c['count']>1]
    return result
