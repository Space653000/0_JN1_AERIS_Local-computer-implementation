"""Materialize and evaluate the canonical 100-seat acoustic capability factory."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from ..config import ROOT
from ..evidence import create_bundle, bundle_dir, seal_bundle, validate_bundle
from . import catalog
from .role_specs import SEAT_SKILLS, product_profile

PACKS=ROOT/"company"/"capabilities"
STATE=ROOT/".aeris"/"capability-factory"
SCHEMA_REQUIRED=("identity","mission","domain","scope","non_scope","inputs","outputs","required_skills",
                 "required_methods","required_knowledge","standards_metadata_references","permitted_tools",
                 "forbidden_actions","risk_authority","evidence_requirements","verification_rubric",
                 "uncertainty_requirements","common_failure_modes","counter_hypotheses","review_requirements",
                 "golden_cases","negative_cases","regression_cases","task_templates","report_templates",
                 "current_maturity_level","maturity_evidence")


def now(): return datetime.now(timezone.utc).isoformat()


def read(path: Path): return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value):
    resolved=path.resolve()
    if not resolved.is_relative_to(ROOT.resolve()): raise ValueError("factory output outside AERIS root")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(catalog.json_value(value),ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def canonical_roles() -> list[dict]:
    from .canonical_registry import load
    groups=load(ROOT)
    result=[]
    for group,names in groups.items():
        for name in names: result.append({"id":f"R{len(result)+1:03d}","name":name,"group":group})
    if len(result)!=100 or len(SEAT_SKILLS)!=100: raise ValueError("100 explicit canonical seat mappings required")
    return result


def pack_digest(pack):
    return catalog.digest({k:v for k,v in pack.items() if k not in {"current_maturity_level","maturity_evidence"}})


def domain_contracts(pack):
    contracts=pack.get('domain_execution_contracts',[])
    if not isinstance(contracts,list):
        raise ValueError('domain_execution_contracts must be an ordered list')
    return contracts


def contract_set_digest(pack):
    """Aggregate-composition digest; never used to stale an unrelated receipt."""
    return catalog.digest(domain_contracts(pack))


def _disk_acceptance_engine_digest():
    names=('factory.py','canonical_registry.py','professional_profiles.py')
    return catalog.digest({name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in names})


def acceptance_engine_digest():
    """Evidence produced by a different maturity predicate cannot be reused."""
    if _disk_acceptance_engine_digest()!=LOADED_ACCEPTANCE_ENGINE_SHA256:
        raise RuntimeError('Maturity predicate changed after load; restart required before evaluation')
    return LOADED_ACCEPTANCE_ENGINE_SHA256


def artifact_digest(pack, cache=None):
    cache={} if cache is None else cache
    paths=[]
    for skill in pack["required_skills"]:
        paths.extend(f"skills/{skill}/{name}" for name in ("SKILL.md","manifest.json","input.schema.json","output.schema.json"))
        paths.append(read(ROOT/f'skills/{skill}/manifest.json')['implementation'])
    paths.extend(contract['suite'] for contract in domain_contracts(pack))
    for key in ("required_methods","required_knowledge","golden_cases","negative_cases","regression_cases","report_templates"):
        paths.extend(pack[key])
    hashes={}
    for relative in paths:
        path=(ROOT/relative).resolve()
        if not path.is_relative_to(ROOT.resolve()): raise ValueError("artifact outside root")
        if relative not in cache: cache[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[relative]=cache[relative]
    return catalog.digest(hashes)


def load_pack(role_id: str):
    if not re.fullmatch(r"R(?:0[0-9]{2}|100)",role_id) or role_id=="R000": raise ValueError("invalid canonical seat ID")
    return read(PACKS/role_id/"capability.json")


def fixture_for(role_id: str, skill_id: str):
    domains=[contract for contract in domain_contracts(load_pack(role_id)) if contract.get('skill_id')==skill_id]
    if len(domains)>1: raise ValueError('duplicate role-domain Skill contract')
    if domains:
        from .role_acceptance import load_contract
        _,suite=load_contract(role_id,skill_id)
        case=next(c for c in suite['cases'] if c['kind']=='positive')
        return {'skill_id':skill_id,'input':{**copy.deepcopy(suite['base_input']),**copy.deepcopy(case['input_overrides'])},
                'checks':copy.deepcopy(case['checks']),'reason':case['question'],
                'source_kind':suite['source_kind'],'scope':suite['scope']}
    fixture=copy.deepcopy(catalog.definitions()[skill_id]["fixture"])
    index=int(role_id[1:])
    if skill_id=="product-system-plan":
        fixture["input"]["product_index"]=index-45
        fixture["input"]["objective"]=f"{load_pack(role_id)['identity']['name']} acoustic architecture and requirement baseline"
        from .cases import check
        fixture["checks"].extend([check("product_index",index-45),check("architecture.speaker_topology_considerations",product_profile(index-45)["speaker_topology_considerations"],unit="text")])
    return fixture


def materialize() -> dict:
    roles=canonical_roles(); definitions=catalog.definitions()
    mappings={skill:[] for skill in definitions}
    for role,skill_names in zip(roles,SEAT_SKILLS):
        for skill in skill_names.split():
            if skill not in mappings: raise ValueError(f"unknown mapped capability: {role['id']} -> {skill}")
            mappings[skill].append(role["id"])
    for skill,definition in definitions.items():
        fixture=definition["fixture"]; folder=ROOT/"skills"/skill
        method_ref=f"methods/engineering/{skill}.json"
        golden_ref=f"golden/engineering/{definition['suite']}/{skill}"
        manifest={"schema_version":1,"skill_id":skill,"version":catalog.VERSION,"factory_contract":True,
                  "implementation":f"skills/{skill}/implementation.py","input_schema":f"skills/{skill}/input.schema.json",
                  "output_schema":f"skills/{skill}/output.schema.json","method":method_ref,
                  "applicability":definition["method_reason"],"assumptions":["inputs meet named SI-unit schema","bounded analytic/synthetic domain, not physical qualification"],
                  "units":"SI quantities in explicitly suffixed fields; dB references declared per method; uncalibrated waveform samples are dimensionless",
                  "uncertainty":"Input measurement uncertainty is not invented; use uncertainty-propagation and repeatability methods when data permits.",
                  "failure_modes":["wrong unit/reference","insufficient excitation or data coverage","nonfinite input","model outside applicability","synthetic results mistaken for measured results"],
                  "golden_tests":golden_ref+"/golden.json","negative_tests":golden_ref+"/negative.json","regression_tests":golden_ref+"/regression.json",
                  "evidence_output":"sealed AERIS bundle with input/output/method/source hashes and numerical check results",
                  "role_mappings":mappings[skill],"tool_layer":"FREE_LOCAL_BASELINE","professional_tool_verified":False}
        write(folder/"manifest.json",manifest)
        write(folder/"input.schema.json",{"$schema":"https://json-schema.org/draft/2020-12/schema",**definition["input_schema"]})
        example=catalog.execute(skill,fixture["input"])
        write(folder/"output.schema.json",catalog.schema_for(example))
        (folder/"implementation.py").write_text(f'"""Version {catalog.VERSION}; {skill} local entrypoint."""\nfrom aeris_runtime.engineering.catalog import execute\n\ndef run(params):\n    return execute({skill!r}, params)\n',encoding="utf-8")
        (folder/"SKILL.md").write_text(f"# {skill}\n\nVersion: {catalog.VERSION}. Tool layer: FREE_LOCAL_BASELINE.\n\n{definition['method_reason']}\n\nInvoke with `python -m aeris_runtime.engineering.factory run-skill {skill} --input PATH`. Inputs must match `input.schema.json`; unknown fields, nonfinite values and out-of-domain values are rejected.\n\nMethod: `{method_ref}`. Analytical, negative and repeated-run cases: `{golden_ref}`.\n\nRaw measurements require source, units, calibration, fixture and uncertainty. Shared synthetic Skill fixtures establish only the stated Skill baseline. Role L3 requires separate role-specific domain acceptance with independent decision oracles and qualified bounded review. L4 requires real instrument/calibration/Human evidence. No proprietary tool execution, physical measurement or formal standards conformance is claimed.\n\nThe factory seals raw input, numerical output, method version, source SHA-256 and check results into an Evidence bundle. Role mappings and failure modes are in the manifest.\n",encoding="utf-8")
        write(ROOT/method_ref,{"method_id":skill,"version":catalog.VERSION,"implementation":definition["implementation"],
                              "applicability":definition["method_reason"],"input_schema":manifest["input_schema"],
                              "assumptions":manifest["assumptions"],"uncertainty":manifest["uncertainty"],"units":manifest["units"],
                              "failure_modes":manifest["failure_modes"],"source_kind":"AERIS_AUTHORED_METHOD_AND_ANALYTICAL_DERIVATION",
                              "reference_urls":["https://docs.scipy.org/doc/scipy-1.15.3/reference/","https://numpy.org/doc/2.2/"],
                              "reference_status":"bibliographic API references; no licensed standard text imported"})
        write(ROOT/golden_ref/"golden.json",{**fixture,"sha256":catalog.digest(fixture)})
        negative={**copy.deepcopy(fixture["input"]),**fixture["negative_patch"]}
        write(ROOT/golden_ref/"negative.json",{"input":negative,"failure_expectation":fixture["failure_expectation"],"sha256":catalog.digest(negative)})
        write(ROOT/golden_ref/"regression.json",{"input":fixture["input"],"expected_checks":fixture["checks"],"require_repeated_output_hash_match":True,"method_version":catalog.VERSION,"sha256":catalog.digest(fixture["input"])})
        note={"id":f"METHOD-{skill}","category":"Methods","title":skill,"text":definition["method_reason"]+" "+manifest["uncertainty"],
              "source":method_ref,"rights":"AERIS_AUTHORED","source_kind":"GENERATED_METHOD_NOTE","is_evidence":False}
        note["sha256"]=hashlib.sha256(note["text"].encode()).hexdigest()
        write(ROOT/"knowledge"/"engineering"/(skill+".json"),note)
    for i,(role,skill_names) in enumerate(zip(roles,SEAT_SKILLS)):
        skills=skill_names.split(); scopes=[definitions[s]["method_reason"] for s in skills]
        pack={"schema_version":1,"identity":role,"mission":role["name"]+": execute and challenge the bounded methods listed in scope.",
              "domain":role["group"],"scope":scopes,"non_scope":["complete human-equivalent specialty competence","real instrumentation/calibration unless separately evidenced","licensed FEM/BEM/CAE or clinical/production approval"],
              "inputs":{s:f"skills/{s}/input.schema.json" for s in skills},"outputs":{s:f"skills/{s}/output.schema.json" for s in skills},
              "required_skills":skills,"required_methods":[f"methods/engineering/{s}.json" for s in skills],
              "required_knowledge":[f"knowledge/engineering/{s}.json" for s in skills],
              "standards_metadata_references":["IEC 60268-5","IEC 60268-4"],"permitted_tools":["FREE_LOCAL_BASELINE","LOCAL_AI_MEMORY_SUMMARY"],
              "forbidden_actions":["modify raw Evidence","invent measurements","claim calibration","self approve R3/R4","launch paid tool","remote private-data upload"],
              "risk_authority":{"automatic":"R0/R1 software only","R2":"controlled local calculation; physical IO gated","R3/R4":"Human Approval required"},
              "evidence_requirements":["input SHA-256","method version and implementation hash","unit/schema validation","numerical output","independent expected-value checks","negative case rejection","repeatable output hash"],
              "verification_rubric":{"L0":"registry only","L1":"complete referenced contract","L2":"all mapped local capabilities executed into intact evidence","L3":"separate role-specific domain acceptance with independent decision oracle and qualified bounded review","L4":"real instrument/calibration/expert approval; cannot be granted by this factory"},
              "uncertainty_requirements":["declare model applicability","separate numerical result from calibration uncertainty","state unavailable uncertainty instead of inventing confidence"],
              "common_failure_modes":["wrong transducer geometry","unexcited or aliased input","units/reference mismatch","model validity exceeded"],
              "counter_hypotheses":["fixture or assembly error rather than product defect","measurement-chain error rather than signal-processing failure","insufficient data rather than a confirmed pass"],
              "review_requirements":{"reviewer":"R098" if role["id"]!="R098" else "R006","evidence_curator":"R099" if role["id"]!="R099" else "R097","automated_review_is_human_approval":False},
              "golden_cases":[f"golden/engineering/{definitions[s]['suite']}/{s}/golden.json" for s in skills],
              "negative_cases":[f"golden/engineering/{definitions[s]['suite']}/{s}/negative.json" for s in skills],
              "regression_cases":[f"golden/engineering/{definitions[s]['suite']}/{s}/regression.json" for s in skills],
              "task_templates":[{"role_id":role["id"],"skill_id":s,"inputs":f"skills/{s}/input.schema.json","risk":"R1","required_evidence":"sealed numerical run"} for s in skills],
              "report_templates":[f"company/capabilities/{role['id']}/report-template.md"],
              "current_maturity_level":"L1","maturity_evidence":[],"canonical_core_sha":read(ROOT/"core.lock.json")["baseline_sha"]}
        if role["group"]=="Product Chiefs": pack["product_architecture"]=product_profile(i-44)
        from .professional_profiles import enrich_pack
        pack=enrich_pack(pack)
        write(PACKS/role["id"]/"capability.json",pack)
        (PACKS/role["id"]/"report-template.md").write_text(f"# {role['id']} {role['name']}\n\n## Engineering objective\n\n## Inputs, units and provenance\n\n## Method and applicability\n\n## Numerical results and requirement margins\n\n## Uncertainty and missing measurements\n\n## Counter-hypotheses and discriminating tests\n\n## Independent review and unresolved disagreement\n\n## Evidence hashes and reproducibility\n\n## Next action and Human Gates\n",encoding="utf-8")
        from .professional_profiles import professional_report_section
        report=PACKS/role['id']/'report-template.md'
        report.write_text(report.read_text(encoding='utf-8')+professional_report_section(pack),encoding='utf-8')
    write(PACKS/"schema.json",{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","required":list(SCHEMA_REQUIRED),"additionalProperties":True})
    write(ROOT/"config"/"engineering_tool_bus.json",{"FREE_LOCAL_BASELINE":{"numpy":"2.2.6","scipy":"1.15.3","skills":list(definitions)},
          "PROFESSIONAL_LICENSED_TOOL":{name:{"state":"OPTIONAL_NOT_INSTALLED_NOT_VERIFIED","interface":{"inputs":["model_or_measurement_contract","tool_version","license_authority"],"outputs":["raw_result","tool_run_log","evidence_hashes"]},"blocks_free_layer":False} for name in ["COMSOL","MATLAB","Ansys/Simcenter","APx","KLIPPEL","SoundCheck","ACQUA"]}})
    corpus=[]
    def knowledge_item(identifier,category,text,source,rights="AERIS_AUTHORED"):
        item={"id":identifier,"category":category,"title":identifier,"text":text,"source":source,"rights":rights,
              "sha256":hashlib.sha256(text.encode()).hexdigest(),"is_evidence":False,"provenance_policy":"source text or generated synthetic derivation; no paywalled standard full text"}
        write(ROOT/"knowledge"/"engineering"/(identifier+".json"),item); corpus.append(item)
    for skill,definition in definitions.items():
        corpus.append(read(ROOT/"knowledge"/"engineering"/(skill+".json")))
        fixture=definition["fixture"]
        knowledge_item("THEORY-"+skill,"Theory",fixture["reason"],f"methods/engineering/{skill}.json")
        knowledge_item("GOLDEN-"+skill,"Golden cases",json.dumps(fixture["checks"],ensure_ascii=False),f"golden/engineering/{definition['suite']}/{skill}/golden.json","SYNTHETIC")
        knowledge_item("FAILURE-"+skill,"Failures",json.dumps({"invalid_variant":fixture["negative_patch"],"expected":fixture["failure_expectation"]},ensure_ascii=False),f"golden/engineering/{definition['suite']}/{skill}/negative.json","SYNTHETIC")
    for i in range(24):
        profile=product_profile(i); role=roles[44+i]
        knowledge_item("PRODUCT-"+role["id"],"Products",json.dumps(profile,ensure_ascii=False),f"company/capabilities/{role['id']}/capability.json")
    for standard in read(ROOT/"standards"/"registry.v1.json")["standards"]:
        identifier="STANDARD-"+re.sub(r"[^A-Za-z0-9_-]","-",standard["standard_id"])
        knowledge_item(identifier,"Standards metadata",json.dumps(standard,ensure_ascii=False),"standards/registry.v1.json","PUBLIC_METADATA")
    for category,text in {
        "Components":"Component-specific sensitivity, geometry, impedance and uncertainty are inputs. No real vendor component data is invented.",
        "Measurements":"Synthetic data is generated by the Golden factory. User measurements require source hash, units, fixture and calibration status.",
        "Root causes":"Use failure-hypotheses to keep support and refutation separate; root cause is not verified from a ranked hypothesis.",
        "Countermeasures":"DFMEA maps ranked risks to named owners and countermeasures; effectiveness requires follow-up evidence.",
        "Lessons":"The Harness derives lessons from source event hashes and retains them as Memory, not original Evidence.",
        "Public research":"provenance-research searches supplied rights-cleared local documents. No patent novelty or freedom-to-operate opinion is produced.",
    }.items(): knowledge_item("POLICY-"+category.replace(" ","-"),category,text,"docs/PROFESSIONAL_COMPANY_BUILD.md")
    write(ROOT/"knowledge"/"engineering"/"manifest.json",{"documents":corpus,"categories":sorted({d['category'] for d in corpus}),"memory_is_evidence":False})
    return {"roles":len(roles),"factory_skills":len(definitions),"methods":len(definitions),"state":"CONTRACTS_MATERIALIZED_NOT_YET_EVALUATED"}


def contract_errors(pack):
    errors=["missing field "+k for k in SCHEMA_REQUIRED if k not in pack]
    from .professional_profiles import profiles
    profile=profiles().get(pack.get('identity',{}).get('id'))
    if profile is None:
        errors.append('unknown professional role identity')
    else:
        for key in ('required_skills','mission','common_failure_modes','counter_hypotheses',
                    'standards_metadata_references','professional_decision_contract','neighbor_distinctions'):
            if pack.get(key)!=profile[key]: errors.append('professional contract mismatch: '+key)
        if pack.get('required_methods')!=profile['professional_decision_contract']['required_methods']:
            errors.append('professional contract mismatch: required_methods')
        if pack.get('domain_execution_contracts')!=profile['domain_execution_contracts']:
            errors.append('professional contract mismatch: domain_execution_contracts')
    try:
        domains=domain_contracts(pack)
        skill_ids=[contract.get('skill_id') for contract in domains if isinstance(contract,dict)]
        suites=[contract.get('suite') for contract in domains if isinstance(contract,dict)]
        if any(not isinstance(contract,dict) or set(contract)!={'skill_id','method','suite','scope'} for contract in domains):
            errors.append('invalid role-domain contract object')
        if len(skill_ids)!=len(set(skill_ids)) or len(suites)!=len(set(suites)):
            errors.append('duplicate role-domain Skill or suite')
    except ValueError as exc:
        domains=[]; errors.append(str(exc))
    definitions=catalog.definitions()
    from .domain_methods import HANDLERS
    for skill in pack.get("required_skills",[]):
        if skill not in definitions and skill not in HANDLERS: errors.append("unknown skill "+skill); continue
        directory=ROOT/"skills"/skill
        for name in ("SKILL.md","manifest.json","input.schema.json","output.schema.json"):
            if not (directory/name).is_file(): errors.append("missing skill asset "+skill+"/"+name)
        if (directory/'manifest.json').is_file():
            manifest=read(directory/'manifest.json'); method=manifest.get('method')
            expected_domains=(profile or {}).get('domain_execution_contracts',[])
            expected_domain=next((item for item in expected_domains if item.get('skill_id')==skill),None)
            expected_method=expected_domain.get('method') if skill in HANDLERS and expected_domain else f'methods/engineering/{skill}.json'
            if method!=expected_method or method not in pack.get('required_methods',[]):
                errors.append('Skill/Method contract mismatch: '+skill)
            implementation='aeris_runtime/engineering/domain_methods.py' if skill in HANDLERS else f'skills/{skill}/implementation.py'
            if manifest.get('implementation')!=implementation or not (ROOT/implementation).is_file():
                errors.append('missing/mismatched Skill implementation: '+skill)
    for key in ("required_methods","required_knowledge","golden_cases","negative_cases","regression_cases","report_templates"):
        for path in pack.get(key,[]):
            candidate=(ROOT/path).resolve()
            if not candidate.is_relative_to(ROOT.resolve()) or not candidate.is_file(): errors.append("missing/unsafe asset "+path)
    return errors


def shared_skill_maturity(pack):
    """Shared fixtures do not prove profession-specific boundary decisions."""
    return 'L0' if contract_errors(pack) else 'L1'


def evaluate_role(role_id: str) -> dict:
    pack=load_pack(role_id); errors=contract_errors(pack)
    if errors: raise ValueError(errors)
    runs=[]
    for skill in shared_skills(pack):
        fixture=fixture_for(role_id,skill)
        output=catalog.execute(skill,fixture["input"])
        checks=catalog.verify_checks(output["values"],fixture["checks"])
        base=catalog.evaluate(skill)
        runs.append({"skill_id":skill,"input":fixture["input"],"output":output,"checks":checks,"evaluation":base,
                     "passed":base["passed"] and all(r["passed"] for r in checks)})
    record={"role_id":role_id,"identity":pack["identity"],"created_at_utc":now(),"contract_sha256":pack_digest(pack),"artifacts_sha256":artifact_digest(pack),
            "acceptance_engine_sha256":acceptance_engine_digest(),"evidence_kind":"SHARED_SKILL_EXECUTION",
            "implementation_sha256":catalog.implementation_digest(),"runs":runs,"all_executable":bool(runs),
            "all_evaluated":all(r["passed"] for r in runs),"scope":"bounded role-mapped synthetic analytical capabilities, not full specialty or physical verification"}
    bundle=create_bundle(f"CAPABILITY-{role_id}","AERIS Capability Factory",method_snapshot={"factory_version":catalog.VERSION,"implementation_sha256":record["implementation_sha256"]})
    run_id=bundle["run_id"]; folder=bundle_dir(run_id)
    write(folder/"processed"/"capability-evaluation.json",record)
    write(folder/"validation.json",{"role_id":role_id,"all_evaluated":record["all_evaluated"],"physical_measurement_verified":False})
    seal_bundle(run_id,"AERIS Capability Factory")
    record_ref={k:v for k,v in record.items() if k!="runs"}
    record_ref.update({"run_id":run_id,"sealed_evidence_ref":str(folder.relative_to(ROOT)),
                       "level":shared_skill_maturity(pack),"shared_skill_baseline_pass":bool(runs) and record["all_evaluated"]})
    write(STATE/"evaluations"/(role_id+".json"),record_ref)
    pack["current_maturity_level"]=record_ref["level"]; pack["maturity_evidence"]=[record_ref["sealed_evidence_ref"]]
    write(PACKS/role_id/"capability.json",pack)
    from .harness import Harness
    Harness().append("CAPABILITY_FACTORY","GOLDEN_REGRESSION",{"role_id":role_id,"passed":record["all_evaluated"],"evidence_run_ids":[run_id],"implementation_sha256":record["implementation_sha256"]},"AERIS Capability Evaluator")
    return record_ref


def matrix() -> dict:
    from .role_acceptance import RoleAcceptanceFactory
    from .domain_methods import HANDLERS
    role_factory=RoleAcceptanceFactory()
    roles=canonical_roles(); rows=[]; counts={f"L{i}":0 for i in range(5)}; groups={}
    implementation=catalog.implementation_digest(); artifact_cache={}
    for role in roles:
        level="L0"; weaknesses=[]; skills=[]; refs=[]; shared_evaluated=False; executable=[]
        domain_status={'execution_passed':False,'case_count':0,'role_l3_accepted':False}
        pack={}
        try:
            pack=load_pack(role["id"]); errors=contract_errors(pack); skills=pack["required_skills"]
            if not errors: level="L1"
            else: weaknesses+=errors
            path=STATE/"evaluations"/(role["id"]+".json")
            if level=="L1" and path.is_file():
                evaluation=read(path)
                if validate_bundle(evaluation["run_id"]).get("valid"):
                    # The unsealed index is a locator, never a source of truth.
                    sealed_path=bundle_dir(evaluation["run_id"])/"processed"/"capability-evaluation.json"
                    sealed=read(sealed_path)
                    expected={"role_id":role["id"],"identity":pack["identity"],
                              "contract_sha256":pack_digest(pack),"artifacts_sha256":artifact_digest(pack,artifact_cache),
                              "implementation_sha256":implementation,"acceptance_engine_sha256":acceptance_engine_digest(),
                              "evidence_kind":"SHARED_SKILL_EXECUTION"}
                    if all(sealed.get(k)==v for k,v in expected.items()) and valid_skill_runs(sealed.get("runs",[]),pack):
                        shared_evaluated=True
                        executable=shared_skills(pack)
                        refs=[str(sealed_path.parent.parent.relative_to(ROOT))]
                    else: weaknesses.append("sealed role/source/contract/predicate mismatch or incomplete Skill/negative evidence")
                else: weaknesses.append("missing or tampered executable evaluation evidence")
            if level=='L1' and domain_contracts(pack):
                domain_status=role_factory.status(role['id'])
                executable.extend(domain_status.get('passed_skill_ids',[]))
                refs.extend(item['evidence_ref'] for item in domain_status.get('capabilities',[]) if item.get('execution_passed'))
                if domain_status['execution_passed']:
                    level=domain_status['level']
                weaknesses.append(domain_status['reason'])
            if level=='L1': weaknesses.append("professional positive/negative/boundary execution not established; shared Skill Golden alone is not role L2 or L3")
            if level in {'L1','L2'}: weaknesses.append('independent role-specific domain acceptance not established')
        except (OSError,ValueError,KeyError,TypeError) as exc: weaknesses.append(str(exc))
        counts[level]+=1
        group=groups.setdefault(role["group"],{"total":0,"L2_or_higher":0,"L3":0})
        group["total"]+=1; group["L2_or_higher"]+=int(level in {"L2","L3","L4"}); group["L3"]+=int(level=="L3")
        rows.append({**role,"level":level,"skills":skills,"executable_skills":sorted(set(executable)),
                      "evidence":refs,"shared_skill_execution_evidenced":shared_evaluated,'domain_execution':domain_status,
                      'domain_capabilities':domain_status.get('capabilities',[]),
                     "coverage":{"skills":len(skills),"methods":len(pack.get('required_methods',[])),
                                 "knowledge":len(pack.get('required_knowledge',[])),"golden":len(pack.get('golden_cases',[])),
                                 "evaluated":len(shared_skills(pack)) if shared_evaluated else 0,
                                  "role_domain_cases":domain_status['case_count'],"role_acceptance":0,
                                  'domain_declared':domain_status.get('declared_capability_count',0),
                                  'domain_passed':domain_status.get('passed_capability_count',0),
                                  'domain_missing':len(domain_status.get('missing_skill_ids',[]))},
                     "known_weaknesses":weaknesses+["no physical/calibrated expert-accepted L4 evidence"]})
    definitions=catalog.definitions(); unresolved=[r["id"] for r in rows if r["level"] in {"L0","L1"}]
    from .professional_profiles import ROLE_DOMAIN_CONTRACTS
    suite_paths=sorted({contract['suite'] for contracts in ROLE_DOMAIN_CONTRACTS.values() for contract in contracts})
    role_suites=[read(ROOT/path) for path in suite_paths]
    return {"assessed_at_utc":now(),"total_roles":100,"maturity_counts":counts,"100_role_L2":100-len(unresolved),
            "total_executable_skills":len(definitions)+len(HANDLERS),"total_methods":len(definitions)+len(HANDLERS),"total_golden_cases":len(definitions),
            "total_role_golden_cases":sum(len(s['cases']) for s in role_suites),'total_role_golden_suites':len(role_suites),
            "total_negative_cases":len(definitions),"total_regression_cases":len(definitions),"coverage_by_group":groups,
            "unresolved_capability_gaps":unresolved,"ROLE_CAN_BE_MADE_L2_WITH_FREE_LOCAL_SOFTWARE":bool(unresolved),
            "roles":rows,"physical_verification_claimed":False,"legacy_registered_skills_not_counted":5,
            "role_acceptance_gaps":[r["id"] for r in rows if r["level"] not in {"L3","L4"}],
            "scope":f"{len(definitions)} shared Skill baselines; independent role-domain acceptance required for L3; no physical/professional verification"}


def shared_skills(pack):
    return [skill for skill in pack['required_skills'] if skill in catalog.definitions()]


def valid_skill_runs(runs, pack):
    """Validate sealed coverage against current fixtures, including negatives."""
    skills=shared_skills(pack)
    if not runs or len(runs)!=len(skills) or {r["skill_id"] for r in runs}!=set(skills): return False
    for run in runs:
        skill=run["skill_id"]; fixture=fixture_for(pack["identity"]["id"],skill)
        output=run["output"]; evaluation=run["evaluation"]
        if not fixture["checks"] or catalog.digest(run["input"])!=catalog.digest(fixture["input"]): return False
        if output.get("skill_id")!=skill or output.get("input_sha256")!=catalog.digest(run["input"]): return False
        if output.get("implementation_sha256")!=catalog.implementation_digest() or output.get("result")!="PASS": return False
        if not all(c["passed"] for c in catalog.verify_checks(output["values"],fixture["checks"])): return False
        if evaluation.get("case_sha256")!=catalog.digest(catalog.definitions()[skill]["fixture"]): return False
        if evaluation.get("implementation_sha256")!=catalog.implementation_digest() or evaluation.get("skill_id")!=skill: return False
        if not evaluation.get("checks") or not all(evaluation.get(k) is True for k in ("golden_pass","negative_pass","regression_pass","passed")): return False
    return True


def main():
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("materialize"); sub.add_parser("evaluate-all"); sub.add_parser("status")
    evaluate=sub.add_parser("evaluate-role"); evaluate.add_argument("role_id")
    run=sub.add_parser("run-skill"); run.add_argument("skill_id"); run.add_argument("--input",required=True)
    args=parser.parse_args()
    if args.command=="materialize": result=materialize()
    elif args.command=="evaluate-role": result=evaluate_role(args.role_id)
    elif args.command=="evaluate-all":
        for role in canonical_roles():
            item=evaluate_role(role["id"]); print(json.dumps({"role":role["id"],"level":item["level"]}),flush=True)
        result=matrix(); write(STATE/"CAPABILITY_MATRIX.json",result)
    elif args.command=="run-skill":
        path=Path(args.input).resolve()
        if not path.is_relative_to(ROOT.resolve()): raise ValueError("input must be inside AERIS root")
        result=catalog.execute(args.skill_id,read(path))
    else:
        result=matrix(); write(STATE/"CAPABILITY_MATRIX.json",result)
    print(json.dumps(catalog.json_value(result),ensure_ascii=False,indent=2))
    return 0


LOADED_ACCEPTANCE_ENGINE_SHA256=_disk_acceptance_engine_digest()


if __name__=="__main__": raise SystemExit(main())
