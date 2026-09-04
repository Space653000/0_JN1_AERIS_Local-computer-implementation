"""Bounded company challenges: actual workflows, independent review and receipts.

Synthetic integration acceptance is neither whole-role L3 nor physical evidence.
"""
from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path
from uuid import uuid4

from .. import evidence, reproduction, controlplane, workflow
from ..config import ROOT
from . import catalog, factory, role_acceptance, domain_review, domain_methods
from .harness import Harness
from .orchestration import run_role
from .professional_profiles import ROLE_DOMAIN_CONTRACTS

REGISTRY = ROOT / 'config/challenges.v1.json'


def inventory():
    return copy.deepcopy(factory.read(REGISTRY)['challenges'])


def load_challenge(identifier):
    for item in inventory():
        if item['id'] == identifier:
            return item
    raise ValueError('unknown challenge ID')


def validate_revision(initial, revised, requirements, allowed):
    if set(initial) != set(revised):
        raise ValueError('revision cannot add or remove fields')
    changed = {key for key in initial if catalog.digest(initial[key]) != catalog.digest(revised[key])}
    if not changed or not changed <= set(allowed) or set(allowed) & set(requirements):
        raise ValueError('nonempty design-only revision required')
    if any(key not in initial or initial[key] != value or revised[key] != value
           for key, value in requirements.items()):
        raise ValueError('immutable requirement changed')


def _current_bindings():
    paths = [Path(__file__), REGISTRY, Path(workflow.__file__), Path(reproduction.__file__),
             ROOT/'aeris_runtime/engineering/orchestration.py', ROOT/'aeris_runtime/engineering/harness.py']
    return {'files': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'domain_source': domain_methods.LOADED_SHA256,
            'acceptance_engine': role_acceptance.engine_digest()}


LOADED_BINDINGS = _current_bindings()


def _bindings():
    current = _current_bindings()
    if current != LOADED_BINDINGS:
        raise RuntimeError('Challenge engine changed after load; restart required')
    return current


def _definition(identifier):
    definition = load_challenge(identifier)
    if not definition['implemented']:
        raise ValueError('SOFTWARE_LOCAL_FIXABLE: challenge not implemented')
    _, suite = role_acceptance.load_contract(definition['role_id'])
    inputs = {}
    for stage in ('initial','revised'):
        case_id=definition.get(stage+'_case_id')
        cases=[case for case in suite['cases'] if case['id']==case_id] if case_id else []
        if case_id and (len(cases)!=1 or cases[0]['kind']=='negative'):
            raise ValueError('challenge must reference one non-negative canonical role scenario')
        scenario=cases[0]['input_overrides'] if cases else {}
        inputs[stage]={**copy.deepcopy(suite['base_input']),**copy.deepcopy(scenario),**definition[stage]}
    validate_revision(inputs['initial'], inputs['revised'], definition['requirements'],
                      definition['allowed_revision_fields'])
    return definition, suite['skill_id'], inputs


def _qualification_roles(role, skill):
    roles = [role]
    for domain in domain_review.REQUIRED_DOMAINS[skill]:
        candidates = [rid for rid, contract in sorted(ROLE_DOMAIN_CONTRACTS.items())
                      if rid != role and factory.read(ROOT/f"skills/{contract['skill_id']}/manifest.json").get('review_domain') == domain]
        if not candidates:
            raise ValueError('missing reviewer implementation: ' + domain)
        roles.append(candidates[0])
    return roles


def _oracles(definition, stage, report):
    values = report['numerical_result']['values']
    checks = catalog.verify_checks(values, definition['oracles'][stage])
    expected = definition['initial_failures'] if stage == 'initial' else []
    failed = [check['id'] for check in values['checks'] if not check['passed']]
    decision = 'DESIGN_REVISION_REQUIRED' if stage == 'initial' else 'BOUNDED_REVIEW_ACCEPT'
    if not checks or not all(c['passed'] for c in checks) or failed != expected or report['review']['decision'] != decision:
        raise ValueError('independent challenge disposition/numerical oracle failed')
    if not values.get('counter_hypotheses'):
        raise ValueError('missing counter-hypothesis')
    return checks


def run(identifier, *, prepare_qualifications=False):
    _bindings()
    definition, skill, inputs = _definition(identifier)
    runner = role_acceptance.RoleAcceptanceFactory()
    roles = _qualification_roles(definition['role_id'], skill)
    before = {role: runner.status(role)['execution_passed'] for role in roles}
    if prepare_qualifications:
        for role, passed in before.items():
            if not passed:
                runner.evaluate(role)
    qualifications = {role: runner.status(role) for role in roles}
    missing = [role for role, item in qualifications.items() if not item['execution_passed']]
    if missing:
        return {'result': 'BLOCKED', 'challenge_id': identifier, 'missing_qualifications': missing,
                'classification': 'SOFTWARE_LOCAL_FIXABLE', 'human_approval': False}
    attempt = 'CHALLENGE-' + uuid4().hex
    project = controlplane.ControlStore().create_project(attempt)['id']
    record = {'attempt_id': attempt, 'project_id': project, 'challenge_id': identifier,
              'bindings': _bindings(), 'definition_sha256': catalog.digest(definition),
              'inputs': inputs, 'skill_id': skill, 'role_id': definition['role_id'],
              'capability_gaps_before': [r for r, ok in before.items() if not ok],
              'qualifications': {r: {'run_id': s['run_id'], 'evidence_ref': s['evidence_ref']} for r, s in qualifications.items()},
              'source_kind': 'SYNTHETIC', 'scope': 'Hypothetical analytical revision; not acquired measurement or physical improvement',
              'role_l3_awarded': False, 'human_approval': False, 'stages': []}
    for stage in ('initial', 'revised'):
        if stage=='revised' and identifier=='FAILURE_FACA':
            record['revision_origin']=_faca_origin(inputs,record['stages'][0]['report'],attempt)
        objective = f'{attempt}/{stage}: {identifier}'
        report = run_role(definition['role_id'], skill, inputs[stage], objective=objective,
                          project_id=project, source_kind='SYNTHETIC',context=definition.get('context'))
        checks = _oracles(definition, stage, report)
        replay = reproduction.reproduce_run(report['evidence_run_id'])
        if replay['result'] != 'PASS':
            raise ValueError('challenge reproduction failed')
        markdown = (factory.STATE/'reports'/(report['workflow_id']+'.md')).read_text(encoding='utf-8')
        record['stages'].append({'stage': stage, 'objective': objective, 'input_sha256': catalog.digest(inputs[stage]),
                                 'report': report, 'report_sha256': catalog.digest(report), 'markdown': markdown,
                                 'reproduction': replay, 'reproduction_sha256': catalog.digest(replay), 'oracles': checks})
    memory = Harness()
    record['memory'] = {'memory_is_evidence': False, 'events': memory.events(project, limit=10000)}
    record['result'] = 'PASS'
    bundle = evidence.create_bundle(attempt, 'AERIS company challenge', run_id=attempt,
                                    requirement_snapshot=definition, method_snapshot=record['bindings'])
    factory.write(evidence.bundle_dir(bundle['run_id'])/'processed/challenge.json', record)
    evidence.seal_bundle(attempt, 'AERIS company challenge')
    verified = status(attempt)
    if not verified['valid']:
        raise ValueError(verified['reason'])
    return {**record, 'run_id': attempt}


def _object(value):
    if not isinstance(value, dict):
        raise ValueError('receipt must be a JSON object')
    return value


def _faca_origin(inputs, first_report, attempt):
    """Read the actual sealed first execution, not caller-authored candidate JSON."""
    from .faca import revision_receipt
    execution_id=first_report['evidence_run_id']
    if not evidence.validate_bundle(execution_id)['valid']:
        raise ValueError('FACA initial execution integrity failed')
    root=evidence.bundle_dir(execution_id)
    context=_object(factory.read(root/'raw/engineering-context.json'))
    output=_object(factory.read(root/'processed/skill_result.json'))
    initial=factory.read(root/'raw/engineering-input.json')
    if (context.get('objective')!=attempt+'/initial: FAILURE_FACA'
            or initial!=inputs['initial'] or output!=first_report['numerical_result']
            or context.get('role_id')!='R094' or context.get('skill_id')!='failure-hypothesis-experiment-baseline'):
        raise ValueError('FACA sealed source belongs to another attempt or model')
    return revision_receipt(initial,inputs['revised'],output['values'],attempt,execution_id)


def _objects(value):
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError('receipt must be a JSON object array')
    return value


def _memory_linkage(events, report, project):
    """Memory witnesses the same task/run; it does not independently prove them."""
    entries = _objects(events)
    if any(event.get('project') != project for event in entries):
        raise ValueError('Memory project mismatch')
    execution = report['evidence_run_id']
    required = {
        'PROJECT_MEMORY': {'task_id': report['task_id'], 'workflow_id': report['workflow_id'], 'role_id': report['role_id']},
        'EXPERIMENT_MEMORY': {'workflow_id': report['workflow_id'], 'evidence_run_ids': [execution]},
        'SKILL_USAGE': {'role_id': report['role_id'], 'skill_id': report['numerical_result']['skill_id'], 'evidence_run_ids': [execution]},
        'CROSS_ROLE_REVIEW': {'review': report['review'], 'evidence_run_ids': [execution, report['review']['review_run_id']]},
    }
    for kind, fields in required.items():
        if not any(event.get('kind') == kind and all(_object(event.get('payload')).get(k) == v for k,v in fields.items()) for event in entries):
            raise ValueError('Memory missing stage linkage: ' + kind)


def status(run_id):
    """Validate receipts against the same attempt, source and live local records."""
    try:
        if not isinstance(run_id, str) or not re.fullmatch(r'CHALLENGE-[0-9a-f]{32}', run_id):
            raise ValueError('invalid challenge run ID')
        if not evidence.validate_bundle(run_id)['valid']:
            raise ValueError('challenge evidence integrity failed')
        root = evidence.bundle_dir(run_id)
        record = _object(factory.read(root/'processed/challenge.json'))
        _object(record['qualifications'])
        _object(record['memory'])
        _objects(record['stages'])
        definition, skill, inputs = _definition(record['challenge_id'])
        if record['attempt_id'] != run_id or record['bindings'] != _bindings() or record['definition_sha256'] != catalog.digest(definition):
            raise ValueError('attempt/source/definition binding mismatch')
        if record['inputs'] != inputs or record['skill_id'] != skill or record['role_id'] != definition['role_id']:
            raise ValueError('input or executor binding mismatch')
        if factory.read(root/'requirement_snapshot.json') != definition or factory.read(root/'method_snapshot.json') != record['bindings']:
            raise ValueError('snapshot mismatch')
        if record['result'] != 'PASS' or record['role_l3_awarded'] is not False or record['human_approval'] is not False or record['source_kind'] != 'SYNTHETIC':
            raise ValueError('unsupported acceptance claim')
        runner = role_acceptance.RoleAcceptanceFactory()
        if set(record['qualifications']) != set(_qualification_roles(definition['role_id'], skill)):
            raise ValueError('qualification seats mismatch')
        for role, receipt in record['qualifications'].items():
            qualification = runner.status(role)
            if not qualification['execution_passed'] or receipt != {key: qualification[key] for key in ('run_id','evidence_ref')}:
                raise ValueError('qualification receipt stale')
        if [item['stage'] for item in record['stages']] != ['initial', 'revised']:
            raise ValueError('two distinct ordered stages required')
        seen = set()
        for item in record['stages']:
            stage, report = item['stage'], _object(item['report'])
            _object(report['review'])
            _object(report['pod'])
            _object(report['numerical_result'])
            _object(item['reproduction'])
            for key, pattern in (('task_id', r'TASK-[A-F0-9]{12}'), ('workflow_id', r'WF-[A-F0-9]{12}'),
                                 ('evidence_run_id', r'RUN-[0-9TZ]+-[a-f0-9]{8}')):
                if not isinstance(report.get(key), str) or not re.fullmatch(pattern, report[key]):
                    raise ValueError('invalid child identifier')
            if not re.fullmatch(r'RUN-[0-9TZ]+-[a-f0-9]{8}', str(report['review'].get('review_run_id', ''))):
                raise ValueError('invalid review identifier')
            objective = f'{run_id}/{stage}: {record["challenge_id"]}'
            task = controlplane.ControlStore().get_task(report['task_id'])
            wf = workflow.load_workflow(report['workflow_id'])
            if (report['task_id'] in seen or item['objective'] != objective or task['title'] != objective
                    or task['project_id'] != record['project_id'] or report['project_id'] != record['project_id']
                    or task['workflow_id'] != report['workflow_id'] or task['state'] != 'EVIDENCED'
                    or report['role_id'] != definition['role_id'] or report['source_kind'] != 'SYNTHETIC'
                    or report['state'] != 'EVIDENCED' or report['human_approval'] is not False):
                raise ValueError('cross-attempt task/report binding mismatch')
            seen.add(report['task_id'])
            if item['input_sha256'] != catalog.digest(inputs[stage]) or item['report_sha256'] != catalog.digest(report):
                raise ValueError('stage digest mismatch')
            path = factory.STATE/'reports'/report['workflow_id']
            if factory.read(path.with_suffix('.json')) != report or path.with_suffix('.md').read_text(encoding='utf-8') != item['markdown']:
                raise ValueError('original report missing or changed')
            execution_id = report['evidence_run_id']
            if not evidence.validate_bundle(execution_id)['valid']:
                raise ValueError('child execution integrity failed')
            child = evidence.bundle_dir(execution_id)
            context = _object(factory.read(child/'raw/engineering-context.json'))
            if (context.get('objective') != objective or context.get('role_id') != definition['role_id']
                    or context.get('skill_id') != skill or context.get('source_kind') != 'SYNTHETIC'
                    or context.get('physical_verification') is not False
                    or report['numerical_result'].get('input_sha256') != item['input_sha256']):
                raise ValueError('sealed execution attempt/context mismatch')
            if (wf['execution']['run_id'] != execution_id or factory.read(child/'run_manifest.json')['task_id'] != wf['task_id']
                    or factory.read(child/'raw/engineering-input.json') != inputs[stage]
                    or factory.read(child/'processed/skill_result.json') != report['numerical_result']):
                raise ValueError('execution linkage mismatch')
            review = report['review']
            if review['execution_run_id'] != execution_id or not domain_review.review_status(review['review_run_id'])['valid']:
                raise ValueError('review receipt invalid')
            sealed_review = factory.read(evidence.bundle_dir(review['review_run_id'])/'processed/domain-review.json')
            if {k:v for k,v in review.items() if k != 'review_run_id'} != sealed_review:
                raise ValueError('report review differs from sealed review')
            if task['pod'] != report['pod'] or report['pod']['executors'] != [definition['role_id']] or not report['pod']['pod_complete']:
                raise ValueError('Pod receipt mismatch')
            for reviewer in review['reviews']:
                if record['qualifications'][reviewer['role_id']]['run_id'] != reviewer['qualification_run_id']:
                    raise ValueError('review qualification linkage mismatch')
            if _oracles(definition, stage, report) != item['oracles']:
                raise ValueError('oracle receipt mismatch')
            replay = item['reproduction']
            replay_path = reproduction.REPRO_ROOT/execution_id/'REPRODUCTION_REPORT.json'
            if (replay['run_id'] != execution_id or replay['result'] != 'PASS' or replay['skill_id'] != skill
                    or item['reproduction_sha256'] != catalog.digest(replay) or factory.read(replay_path) != replay
                    or replay['expected_sha256'] != catalog.digest(report['numerical_result'])
                    or replay['actual_sha256'] != replay['expected_sha256']):
                raise ValueError('reproduction receipt mismatch')
            _memory_linkage(record['memory']['events'], report, record['project_id'])
        if record['challenge_id']=='FAILURE_FACA':
            origin=_faca_origin(inputs,record['stages'][0]['report'],run_id)
            if record.get('revision_origin')!=origin:
                raise ValueError('FACA revision origin receipt mismatch')
        memory = Harness()
        if (record['memory']['memory_is_evidence'] is not False or not memory.verify()['valid']
                or record['memory']['events'] != memory.events(record['project_id'], limit=10000)):
            raise ValueError('Memory source receipt mismatch')
        return {'valid': True, 'result': 'PASS', 'run_id': run_id, 'role_l3_awarded': False}
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        return {'valid': False, 'result': 'FAIL', 'reason': str(exc)}


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inventory', 'run', 'status'))
    parser.add_argument('identifier', nargs='?')
    parser.add_argument('--prepare-qualifications', action='store_true')
    args = parser.parse_args()
    if args.action != 'inventory' and not args.identifier:
        parser.error('identifier required')
    result = inventory() if args.action == 'inventory' else status(args.identifier) if args.action == 'status' else run(args.identifier, prepare_qualifications=args.prepare_qualifications)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if isinstance(result, list) or result.get('result') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
