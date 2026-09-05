"""Sealed profession-specific execution; never substitute Skill PASS for L3.

Index files are locators. The current role/Method/suite/source contracts and
replayed decision oracles are authoritative. Qualified review is a separate
gate: this execution stage cannot award L3 or physical acceptance.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sqlite3
from contextlib import closing
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
           ROOT/'aeris_runtime/skills_runtime.py',ROOT/'aeris_runtime/evidence.py')
    return catalog.digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def _contract_for(pack,skill_id=None):
    contracts=factory.domain_contracts(pack)
    if not contracts: raise ValueError('role-specific execution contract not yet implemented')
    if skill_id is None:
        if len(contracts)!=1: raise ValueError('explicit Skill ID required for multi-capability role')
        return contracts[0]
    matches=[contract for contract in contracts if contract.get('skill_id')==skill_id]
    if len(matches)!=1: raise ValueError('unknown or duplicate role-domain Skill contract')
    return matches[0]


def load_contract(role_id,skill_id=None):
    pack=factory.load_pack(role_id)
    errors=factory.contract_errors(pack)
    if errors: raise ValueError(errors)
    contract=_contract_for(pack,skill_id)
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


def capability_artifact_digest(pack,contract,suite):
    """Hash only artifacts capable of changing this exact capability verdict."""
    manifest=factory.read(ROOT/f"skills/{contract['skill_id']}/manifest.json")
    paths=[contract['method'],contract['suite'],
           *(f"skills/{contract['skill_id']}/{name}" for name in
             ('SKILL.md','manifest.json','input.schema.json','output.schema.json'))]
    hashes={}
    for relative in paths:
        path=(ROOT/relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError('missing or unsafe capability artifact: '+relative)
        hashes[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
    if catalog.digest(suite)!=catalog.digest(factory.read(ROOT/contract['suite'])):
        raise ValueError('loaded suite differs from declared capability artifact')
    return catalog.digest({'files':hashes,'implementation':manifest['implementation'],
                           'implementation_source_sha256':domain_methods.capability_source_digest(contract['skill_id'])})


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

    def _bindings(self,pack,contract,suite):
        if engine_digest()!=LOADED_ENGINE_SHA256:
            raise RuntimeError('Role acceptance engine changed after load; restart required')
        factory.acceptance_engine_digest()
        method_path=(ROOT/contract['method']).resolve()
        return {'role_id':pack['identity']['id'],'identity':pack['identity'],
                'role_identity_sha256':catalog.digest(pack['identity']),
                'skill_id':contract['skill_id'],'method':contract['method'],'suite':contract['suite'],
                'contract_sha256':catalog.digest(contract),
                'artifacts_sha256':capability_artifact_digest(pack,contract,suite),
                'suite_sha256':catalog.digest(suite),'method_source_sha256':hashlib.sha256(method_path.read_bytes()).hexdigest(),
                'engine_sha256':LOADED_ENGINE_SHA256,'review_policy_sha256':catalog.digest(REVIEW_POLICY),
                'evidence_kind':'ROLE_DOMAIN_EXECUTION','source_kind':suite['source_kind']}

    def _locator(self,role_id,skill_id):
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}',skill_id):
            raise ValueError('invalid Skill evidence locator')
        path=(self.state_root/role_id/(skill_id+'.json')).resolve()
        if not path.is_relative_to(self.state_root): raise ValueError('role evidence locator outside state root')
        return path

    def _composition_db(self):
        path=(self.state_root/'composition.sqlite3').resolve()
        if not path.is_relative_to(self.state_root): raise ValueError('composition history outside state root')
        return path

    def _composition_anchor_dir(self,role_id):
        path=(self.state_root/'composition-anchors'/role_id).resolve()
        if not path.is_relative_to(self.state_root): raise ValueError('composition anchor outside state root')
        return path

    def _has_capability_locator(self,role_id):
        folder=(self.state_root/role_id).resolve()
        return folder.is_dir() and any(path.name!='composition.jsonl' for path in folder.glob('*.json'))

    def _anchor_map(self,role_id,history,require_complete):
        folder=self._composition_anchor_dir(role_id); anchors={}
        if folder.is_dir():
            for path in folder.glob('*.json'):
                locator=factory.read(path); sequence=locator.get('sequence')
                if (not isinstance(sequence,int) or sequence<1 or sequence>len(history)
                        or sequence in anchors or locator.get('record_sha256')!=history[sequence-1]['record_sha256']):
                    raise ValueError('composition anchor does not match ledger history')
                run_id=locator.get('run_id')
                if not isinstance(run_id,str) or not evidence.validate_bundle(run_id).get('valid'):
                    raise ValueError('composition anchor Evidence invalid')
                sealed=factory.read(evidence.bundle_dir(run_id)/'processed/role-composition-anchor.json')
                if sealed!=history[sequence-1]: raise ValueError('composition anchor payload mismatch')
                anchors[sequence]=locator
        if require_complete and set(anchors)!=set(range(1,len(history)+1)):
            raise ValueError('composition ledger missing sealed anchor')
        return anchors

    def _ensure_composition_anchors(self,role_id,history):
        anchors=self._anchor_map(role_id,history,False); folder=self._composition_anchor_dir(role_id)
        for record in history:
            sequence=record['sequence']
            if sequence in anchors: continue
            bundle=evidence.create_bundle('ROLE-COMPOSITION-'+role_id,'Role Acceptance Factory',
                requirement_snapshot={'role_id':role_id,'sequence':sequence,'contract_set_sha256':record['contract_set_sha256']},
                method_snapshot={'record_sha256':record['record_sha256'],'authority':'APPEND_ONLY_SQLITE_PLUS_SEALED_EVIDENCE'})
            run_id=bundle['run_id']; factory.write(evidence.bundle_dir(run_id)/'processed/role-composition-anchor.json',record)
            evidence.seal_bundle(run_id,'Role Acceptance Factory')
            locator={'sequence':sequence,'record_sha256':record['record_sha256'],'run_id':run_id}
            path=folder/(f"{sequence:06d}-{record['record_sha256']}.json")
            folder.mkdir(parents=True,exist_ok=True)
            try:
                with path.open('x',encoding='utf-8',newline='\n') as stream:
                    stream.write(json.dumps(locator,ensure_ascii=False,separators=(',',':'))+'\n')
            except FileExistsError:
                existing=factory.read(path)
                if (existing.get('sequence')!=sequence or existing.get('record_sha256')!=record['record_sha256']
                        or not evidence.validate_bundle(existing.get('run_id','')).get('valid')):
                    raise ValueError('conflicting immutable composition anchor')
        self._anchor_map(role_id,history,True)

    @staticmethod
    def _history_rows(role_id,rows):
        history=[]; previous=None; identity_sha256=catalog.digest(factory.load_pack(role_id)['identity'])
        for number,(sequence,contract_set_sha256,record_sha256,record_json) in enumerate(rows,1):
            record=json.loads(record_json)
            required={'sequence','role_id','role_identity_sha256','contract_set_sha256','contracts',
                      'observed_at_utc','previous_record_sha256','record_sha256'}
            if (not isinstance(record,dict) or set(record)!=required or sequence!=number
                    or record['sequence']!=sequence or record['role_id']!=role_id
                    or record['contract_set_sha256']!=contract_set_sha256
                    or record['record_sha256']!=record_sha256
                    or record['role_identity_sha256']!=identity_sha256
                    or not isinstance(record['contracts'],list)
                    or any(not isinstance(contract,dict) or set(contract)!={'skill_id','method','suite','scope'} for contract in record['contracts'])
                    or catalog.digest(record['contracts'])!=contract_set_sha256
                    or record['previous_record_sha256']!=previous):
                raise ValueError('invalid composition history chain')
            body={key:value for key,value in record.items() if key!='record_sha256'}
            if record['record_sha256']!=catalog.digest(body):
                raise ValueError('tampered composition history record')
            previous=record['record_sha256']; history.append(record)
        return history

    def _initialize_composition_db(self,connection):
        connection.executescript('''
            CREATE TABLE IF NOT EXISTS composition(
                role_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                contract_set_sha256 TEXT NOT NULL, record_sha256 TEXT NOT NULL,
                record_json TEXT NOT NULL, PRIMARY KEY(role_id,sequence));
            CREATE TRIGGER IF NOT EXISTS composition_no_update
                BEFORE UPDATE ON composition BEGIN SELECT RAISE(ABORT,'composition history is append-only'); END;
            CREATE TRIGGER IF NOT EXISTS composition_no_delete
                BEFORE DELETE ON composition BEGIN SELECT RAISE(ABORT,'composition history is append-only'); END;
        ''')

    def composition_history(self,role_id):
        path=self._composition_db()
        if not path.is_file(): return []
        with closing(sqlite3.connect(path)) as connection:
            self._initialize_composition_db(connection)
            rows=connection.execute('SELECT sequence,contract_set_sha256,record_sha256,record_json FROM composition WHERE role_id=? ORDER BY sequence',(role_id,)).fetchall()
        history=self._history_rows(role_id,rows)
        self._anchor_map(role_id,history,True)
        return history

    def _observe_composition(self,pack):
        role_id=pack['identity']['id']; path=self._composition_db(); path.parent.mkdir(parents=True,exist_ok=True)
        current=factory.contract_set_digest(pack)
        with closing(sqlite3.connect(path,timeout=15)) as connection:
            self._initialize_composition_db(connection)
            connection.execute('BEGIN IMMEDIATE')
            rows=connection.execute('SELECT sequence,contract_set_sha256,record_sha256,record_json FROM composition WHERE role_id=? ORDER BY sequence',(role_id,)).fetchall()
            history=self._history_rows(role_id,rows)
            if not history and self._has_capability_locator(role_id):
                raise ValueError('composition ledger missing for existing capability Evidence')
            self._anchor_map(role_id,history,False)
            if history and history[-1]['contract_set_sha256']==current:
                connection.commit()
                self._ensure_composition_anchors(role_id,history)
                return history
            body={'sequence':len(history)+1,'role_id':role_id,
                  'role_identity_sha256':catalog.digest(pack['identity']),
                  'contract_set_sha256':current,'contracts':copy.deepcopy(factory.domain_contracts(pack)),
                  'observed_at_utc':factory.now(),
                  'previous_record_sha256':history[-1]['record_sha256'] if history else None}
            record={**body,'record_sha256':catalog.digest(body)}
            encoded=json.dumps(catalog.json_value(record),ensure_ascii=False,separators=(',',':'),allow_nan=False)
            connection.execute('INSERT INTO composition VALUES(?,?,?,?,?)',
                               (role_id,record['sequence'],current,record['record_sha256'],encoded))
            connection.commit()
        result=[*history,record]
        self._ensure_composition_anchors(role_id,result)
        return result

    def evaluate(self,role_id,skill_id=None):
        pack,suite=load_contract(role_id,skill_id)
        contract=_contract_for(pack,suite['skill_id'])
        self._observe_composition(pack)
        bindings=self._bindings(pack,contract,suite); cases=execute_cases(suite)
        record={**bindings,'cases':cases,'created_at_utc':factory.now(),'scope':suite['scope']}
        bundle=evidence.create_bundle('ROLE-DOMAIN-'+role_id+'-'+contract['skill_id'],'Role Acceptance Factory',
            requirement_snapshot={'questions':[c['question'] for c in suite['cases']]},method_snapshot=bindings)
        run_id=bundle['run_id']; folder=evidence.bundle_dir(run_id)
        factory.write(folder/'processed/role-domain-execution.json',record)
        evidence.seal_bundle(run_id,'Role Acceptance Factory')
        factory.write(self._locator(role_id,contract['skill_id']),
                      {'role_id':role_id,'skill_id':contract['skill_id'],'run_id':run_id})
        return self.status_for_skill(role_id,contract['skill_id'])

    def status_for_skill(self,role_id,skill_id):
        pack=factory.load_pack(role_id)
        result={'role_id':role_id,'level':'L0' if factory.contract_errors(pack) else 'L1',
                'skill_id':skill_id,
                'execution_passed':False,'role_l3_accepted':False,'review_state':'REVIEW_BLOCKED',
                'physical_measurement_verified':False,'case_count':0,'reason':'No current role-domain execution evidence'}
        index=self._locator(role_id,skill_id)
        if not index.is_file(): return result
        try:
            pack,suite=load_contract(role_id,skill_id); contract=_contract_for(pack,skill_id)
            locator=factory.read(index); run_id=locator['run_id']
            if locator.get('role_id')!=role_id or locator.get('skill_id')!=skill_id:
                raise ValueError('role/Skill evidence locator mismatch')
            if not isinstance(run_id,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,139}',run_id):
                raise ValueError('invalid evidence locator')
            if not evidence.validate_bundle(run_id).get('valid'): raise ValueError('missing or tampered role evidence')
            path=evidence.bundle_dir(run_id)/'processed/role-domain-execution.json'
            record=factory.read(path)
            if any(record.get(k)!=v for k,v in self._bindings(pack,contract,suite).items()):
                raise ValueError('sealed role/source/Method/suite/review-policy mismatch')
            replay=execute_cases(suite)
            if catalog.digest(record.get('cases'))!=catalog.digest(replay):
                raise ValueError('role decision replay mismatch')
            passed=bool(replay) and all(c['passed'] for c in replay)
            result.update(level='L2' if passed else 'L1',execution_passed=passed,
                          case_count=len(replay),run_id=run_id,scope=suite['scope'],
                          evidence_ref=str(path.relative_to(ROOT)),
                          reason='Bounded domain execution evidenced; qualified independent review still required' if passed else 'Role decision checks failed')
        except (OSError,ValueError,KeyError,TypeError,RuntimeError) as exc:
            result['reason']=str(exc)
        return result

    def status(self,role_id):
        pack=factory.load_pack(role_id); errors=factory.contract_errors(pack)
        try: contracts=factory.domain_contracts(pack)
        except ValueError as exc: errors=[*errors,str(exc)]; contracts=[]
        composition=[]; composition_error=None
        if not errors and (contracts or self._composition_db().is_file()):
            try: composition=self._observe_composition(pack)
            except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,sqlite3.DatabaseError) as exc:
                composition_error=str(exc)
        capabilities=[]
        for contract in contracts:
            skill_id=contract.get('skill_id') if isinstance(contract,dict) else ''
            capabilities.append(self.status_for_skill(role_id,skill_id) if skill_id else {
                'role_id':role_id,'skill_id':skill_id,'level':'L0','execution_passed':False,
                'case_count':0,'reason':'invalid role-domain Skill contract'})
        passed=[item for item in capabilities if item.get('execution_passed')]
        all_passed=bool(contracts) and len(passed)==len(contracts) and not errors and not composition_error
        level='L0' if errors else 'L2' if all_passed else 'L1'
        missing=[contract.get('skill_id') for contract,item in zip(contracts,capabilities) if not item.get('execution_passed')]
        missing_reasons=[item.get('reason','missing current Evidence') for item in capabilities if not item.get('execution_passed')]
        result={'role_id':role_id,'level':level,'execution_passed':all_passed,
                'role_l3_accepted':False,'review_state':'REVIEW_BLOCKED',
                'physical_measurement_verified':False,'case_count':sum(item.get('case_count',0) for item in passed),
                'contract_set_sha256':factory.contract_set_digest(pack) if not errors else None,
                'composition_history_valid':composition_error is None,
                'composition_history':[{'sequence':item['sequence'],'contract_set_sha256':item['contract_set_sha256'],
                                        'record_sha256':item['record_sha256']} for item in composition],
                'declared_capability_count':len(contracts),'passed_capability_count':len(passed),
                'passed_skill_ids':[item['skill_id'] for item in passed],
                'missing_skill_ids':missing,'capabilities':capabilities,
                'reason':('Invalid role contract: '+'; '.join(errors) if errors else
                          'Composition history invalid: '+composition_error if composition_error else
                          'No role-specific domain capability declared' if not contracts else
                          'All declared bounded domain capabilities evidenced; independent role-specific L3 acceptance remains required' if all_passed else
                          'Partial role-domain execution only; missing current Evidence for: '+', '.join(missing)+
                          ' ('+'; '.join(missing_reasons)+')')}
        if len(capabilities)==1:
            for key in ('run_id','evidence_ref','scope'):
                if key in capabilities[0]: result[key]=capabilities[0][key]
        return result


LOADED_ENGINE_SHA256=engine_digest()


def main():
    import argparse
    import json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['evaluate','status'])
    parser.add_argument('role_id')
    parser.add_argument('--skill')
    args=parser.parse_args()
    runner=RoleAcceptanceFactory()
    result=runner.evaluate(args.role_id,args.skill) if args.action=='evaluate' else (runner.status_for_skill(args.role_id,args.skill) if args.skill else runner.status(args.role_id))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if args.action=='status' or result['execution_passed'] else 1


if __name__=='__main__': raise SystemExit(main())
