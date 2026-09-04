"""Sealed profession-specific execution; never substitute Skill PASS for L3.

Index files are locators. The current role/Method/suite/source contracts and
replayed decision oracles are authoritative. Qualified review is a separate
gate: this execution stage cannot award L3 or physical acceptance.
"""
from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path

from .. import evidence
from ..config import ROOT
from ..skills_runtime import run_skill
from . import catalog, domain_methods, factory

REVIEW_POLICY={'version':'H0001-domain-execution-v1','required':'separately evidenced qualified bounded reviewer',
               'missing_review':'REVIEW_BLOCKED','execution_stage_maximum':'L2',
               'automated_seat_is_human_approval':False}
STATE=ROOT/'.aeris/role-acceptance'


def _mutation_path_valid(path):
    return (isinstance(path,str) and bool(path)
            and all(part.isdigit() or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',part) for part in path.split('.')))


def apply_case_mutations(target,mutations):
    if (not isinstance(mutations,list) or len(mutations)>40
            or any(not isinstance(m,dict) or set(m)!={'path','value'} or not _mutation_path_valid(m['path']) for m in mutations)
            or len({m['path'] for m in mutations})!=len(mutations)):
        raise ValueError('bounded unique input mutation paths required')
    for mutation in mutations:
        parts=mutation['path'].split('.');current=target
        for part in parts[:-1]:
            current=current[int(part)] if isinstance(current,list) and part.isdigit() else current[part]
        final=parts[-1]
        if isinstance(current,list) and final.isdigit():
            index=int(final)
            if not 0<=index<len(current):raise ValueError('mutation list index outside fixture')
            current[index]=copy.deepcopy(mutation['value'])
        else:
            if not isinstance(current,dict) or final not in current:raise ValueError('mutation field outside fixture')
            current[final]=copy.deepcopy(mutation['value'])
    return target


def engine_digest():
    paths=(Path(__file__),Path(factory.__file__),Path(catalog.__file__),
           ROOT/'aeris_runtime/skills_runtime.py',ROOT/'aeris_runtime/evidence.py',
           ROOT/'aeris_runtime/engineering/professional_profiles.py')
    return catalog.digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def load_contract(role_id):
    pack=factory.load_pack(role_id)
    errors=factory.contract_errors(pack)
    if errors: raise ValueError(errors)
    contract=pack.get('domain_execution_contract')
    if not contract: raise ValueError('role-specific execution contract not yet implemented')
    path=(ROOT/contract['suite']).resolve()
    if not path.is_relative_to((ROOT/'golden/roles'/role_id).resolve()):
        raise ValueError('role suite outside its canonical seat directory')
    suite=factory.read(path)
    if suite.get('role_id')!=role_id or suite.get('skill_id')!=contract['skill_id']:
        raise ValueError('role/Skill/suite mismatch')
    manifest=factory.read(ROOT/f"skills/{contract['skill_id']}/manifest.json")
    if role_id not in manifest.get('role_mappings',[]) or manifest.get('method')!=contract['method']:
        raise ValueError('domain Method/Skill role binding mismatch')
    cases=suite.get('cases',[])
    if not {'positive','negative','boundary','counter_hypothesis'}<={c.get('kind') for c in cases}:
        raise ValueError('positive, negative, boundary and counter-hypothesis cases required')
    ids=[c.get('id') for c in cases]
    if any(not isinstance(i,str) or not i for i in ids) or len(set(ids))!=len(ids):
        raise ValueError('nonempty unique role case IDs required')
    for case in cases:
        if not case.get('question') or not isinstance(case.get('input_overrides'),dict):
            raise ValueError('role decision question and declared input patch required')
        mutations=case.get('input_mutations',[])
        if (not isinstance(mutations,list) or len(mutations)>40
                or any(not isinstance(m,dict) or set(m)!={'path','value'} or not _mutation_path_valid(m['path']) for m in mutations)
                or len({m['path'] for m in mutations})!=len(mutations)):
            raise ValueError('bounded unique input mutation paths required')
        if case['kind']=='negative':
            if case.get('expected_error')!='ValueError' or case.get('checks'):
                raise ValueError('negative case must declare invalid-input rejection')
        elif not case.get('checks') or case.get('expected_error'):
            raise ValueError('independent decision checks required for every non-negative case')
    if not suite.get('oracle_provenance') or suite.get('source_kind')!='SYNTHETIC':
        raise ValueError('explicit synthetic oracle provenance required')
    return pack,suite


def execute_cases(suite):
    results=[]
    for case in suite['cases']:
        params={**copy.deepcopy(suite['base_input']),**copy.deepcopy(case['input_overrides'])}
        apply_case_mutations(params,case.get('input_mutations',[]))
        outcomes=[]
        for _ in range(2):
            try:
                output=run_skill(suite['skill_id'],params)
                checks=catalog.verify_checks(output['values'],case.get('checks',[]))
                outcomes.append({'output':output,'checks':checks,
                    'passed':case['kind']!='negative' and bool(checks) and all(c['passed'] for c in checks)})
            except ValueError:
                outcomes.append({'error':'ValueError','passed':case['kind']=='negative'})
        repeat=catalog.digest(outcomes[0])==catalog.digest(outcomes[1])
        results.append({'case_id':case['id'],'kind':case['kind'],'question':case['question'],
                        'input':params,'input_sha256':catalog.digest(params),**outcomes[0],
                        'repeatable':repeat,'passed':outcomes[0]['passed'] and repeat})
    return results


class RoleAcceptanceFactory:
    def __init__(self,state_root=None):
        self.state_root=Path(state_root or STATE).resolve()
        if not self.state_root.is_relative_to((ROOT/'.aeris').resolve()):
            raise ValueError('role acceptance state must stay inside local .aeris')

    def _bindings(self,pack,suite):
        if engine_digest()!=LOADED_ENGINE_SHA256:
            raise RuntimeError('Role acceptance engine changed after load; restart required')
        factory.acceptance_engine_digest()
        return {'role_id':pack['identity']['id'],'identity':pack['identity'],
                'contract_sha256':factory.pack_digest(pack),'artifacts_sha256':factory.artifact_digest(pack),
                'suite_sha256':catalog.digest(suite),'method_source_sha256':domain_methods.LOADED_SHA256,
                'engine_sha256':LOADED_ENGINE_SHA256,'review_policy_sha256':catalog.digest(REVIEW_POLICY),
                'evidence_kind':'ROLE_DOMAIN_EXECUTION','source_kind':suite['source_kind']}

    def evaluate(self,role_id):
        pack,suite=load_contract(role_id)
        bindings=self._bindings(pack,suite); cases=execute_cases(suite)
        record={**bindings,'cases':cases,'created_at_utc':factory.now(),'scope':suite['scope']}
        bundle=evidence.create_bundle('ROLE-DOMAIN-'+role_id,'Role Acceptance Factory',
            requirement_snapshot={'questions':[c['question'] for c in suite['cases']]},method_snapshot=bindings)
        run_id=bundle['run_id']; folder=evidence.bundle_dir(run_id)
        factory.write(folder/'processed/role-domain-execution.json',record)
        evidence.seal_bundle(run_id,'Role Acceptance Factory')
        factory.write(self.state_root/(role_id+'.json'),{'role_id':role_id,'run_id':run_id})
        return self.status(role_id)

    def status(self,role_id):
        pack=factory.load_pack(role_id)
        result={'role_id':role_id,'level':'L0' if factory.contract_errors(pack) else 'L1',
                'execution_passed':False,'role_l3_accepted':False,'review_state':'REVIEW_BLOCKED',
                'physical_measurement_verified':False,'case_count':0,'reason':'No current role-domain execution evidence'}
        index=self.state_root/(role_id+'.json')
        if not index.is_file(): return result
        try:
            pack,suite=load_contract(role_id)
            locator=factory.read(index); run_id=locator['run_id']
            if not isinstance(run_id,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,139}',run_id):
                raise ValueError('invalid evidence locator')
            if not evidence.validate_bundle(run_id).get('valid'): raise ValueError('missing or tampered role evidence')
            path=evidence.bundle_dir(run_id)/'processed/role-domain-execution.json'
            record=factory.read(path)
            if any(record.get(k)!=v for k,v in self._bindings(pack,suite).items()):
                raise ValueError('sealed role/source/Method/suite/review-policy mismatch')
            replay=execute_cases(suite)
            if catalog.digest(record.get('cases'))!=catalog.digest(replay):
                raise ValueError('role decision replay mismatch')
            passed=bool(replay) and all(c['passed'] for c in replay)
            result.update(level='L2' if passed else 'L1',execution_passed=passed,
                          case_count=len(replay),run_id=run_id,scope=suite['scope'],
                          evidence_ref=str(path.relative_to(ROOT)),
                          reason='Bounded domain execution evidenced; qualified independent review still required' if passed else 'Role decision checks failed')
        except (OSError,ValueError,KeyError,TypeError) as exc:
            result['reason']=str(exc)
        return result


LOADED_ENGINE_SHA256=engine_digest()


def main():
    import argparse
    import json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['evaluate','status'])
    parser.add_argument('role_id')
    args=parser.parse_args()
    runner=RoleAcceptanceFactory()
    result=runner.evaluate(args.role_id) if args.action=='evaluate' else runner.status(args.role_id)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if args.action=='status' or result['execution_passed'] else 1


if __name__=='__main__': raise SystemExit(main())
