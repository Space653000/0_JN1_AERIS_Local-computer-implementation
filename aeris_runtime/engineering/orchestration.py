"""Capability-based Pod coverage and real SQLite/workflow/evidence execution."""
from __future__ import annotations

from ..config import ROOT
from ..evidence import validate_bundle
from . import catalog, factory
from .harness import Harness


def route_pod(request: dict, capability_matrix=None):
    required=request.get("needed_skills",[])
    if not isinstance(required,list) or not required or any(s not in catalog.definitions() for s in required):
        raise ValueError("explicit known needed_skills required; keyword-only routing is not supported")
    request={**request,"transducer":{"speaker":"Speaker","microphone":"Microphone","both":"Both"}.get(request.get("transducer"),request.get("transducer"))}
    if request.get("transducer") not in {"Speaker","Microphone","Both"}: raise ValueError("transducer must be Speaker, Microphone or Both")
    if request.get("lifecycle") not in {"Concept","Architecture","Prototype","EVT","DVT","PVT","MP","Field","Field Return"}: raise ValueError("canonical lifecycle required")
    risk=request.get("risk","R1")
    if risk not in {"R0","R1","R2","R3","R4"}: raise ValueError("unknown risk")
    if not str(request.get("requirement","")).strip() or not request.get("required_evidence"):
        raise ValueError("Requirement and required evidence must be declared")
    if "FREE_LOCAL_BASELINE" not in request.get("available_tools",[]):
        return {"state":"BLOCKED","uncovered_skills":required,"reason":"free local tool layer unavailable","roles":[],"pod_size":0}
    matrix=capability_matrix or factory.matrix()
    eligible=[r for r in matrix["roles"] if r["level"] in {"L2","L3","L4"}]
    by_id={r["id"]:r for r in eligible}; remaining=set(required); executors=[]; reasons={}
    group={"Speaker":"Speaker CoE","Microphone":"Microphone CoE"}.get(request["transducer"])
    while remaining:
        candidates=[r for r in eligible if r["id"] not in {x["id"] for x in executors} and r["id"] not in {"R098","R099"} and remaining & set(r["skills"])]
        if not candidates: break
        selected=sorted(candidates,key=lambda r:(-len(remaining&set(r["skills"])), -int(r["group"]==group),r["id"]))[0]
        covers=sorted(remaining & set(selected["skills"])); remaining-=set(covers)
        executors.append(selected); reasons[selected["id"]]="Executable "+selected["level"]+" coverage: "+", ".join(covers)
    product=request.get("product","")
    chiefs=[r for r in eligible if r["group"]=="Product Chiefs" and product in {r["id"],r["name"]}]
    lead=chiefs[0] if chiefs else (by_id.get("R001") or (executors[0] if executors else None))
    reviewer=by_id.get("R098"); curator=by_id.get("R099")
    if lead: reasons.setdefault(lead["id"],"Product-specific authority" if chiefs else "Cross-domain requirement/architecture lead")
    if reviewer: reasons[reviewer["id"]]="Independent counter-hypothesis and Evidence-claim checks; not Human approval"
    if curator: reasons[curator["id"]]="Evidence hashes, traceability and knowledge provenance"
    selected=[]
    for role in [lead,*executors,reviewer,curator]:
        if role and role["id"] not in {r["id"] for r in selected}: selected.append({**role,"selection_reason":reasons[role["id"]]})
    blocked=bool(remaining or not reviewer or not curator or not lead)
    return {"state":"BLOCKED" if blocked else "PLANNED","planner":"capability_coverage_and_maturity_v1","pod_size":len(selected),
            "roles":selected,"lead":lead["id"] if lead else None,"executors":[r["id"] for r in executors],
            "reviewer":reviewer["id"] if reviewer else None,"evidence_curator":curator["id"] if curator else None,
            "uncovered_skills":sorted(remaining),"human_approval_required":risk in {"R2","R3","R4"},"request":request}


def run_role(role_id: str, skill_id: str, params: dict, *, objective: str, project_id=None, risk="R1", source_kind="USER_SUPPLIED_UNVERIFIED", context=None):
    from ..controlplane import ControlStore
    from ..workflow import create_engineering_workflow, execute_workflow, _write
    pack=factory.load_pack(role_id)
    if skill_id not in pack["required_skills"]: raise ValueError("requested Skill outside this seat's contracted scope")
    if risk not in {"R0","R1"}: raise ValueError("this automatic path permits only R0/R1 local software; higher-risk approval must be explicit")
    if source_kind not in {"SYNTHETIC","USER_SUPPLIED_UNVERIFIED"}: raise ValueError("cannot self-assert calibrated/verified data")
    # Validate before creating an operational task; malformed requests must not leave orphan tasks.
    catalog.validate(params,catalog.definitions()[skill_id]["input_schema"])
    if context is not None and (not isinstance(context,dict) or set(context)-{"product","transducer","lifecycle","requirement","required_evidence"}):
        raise ValueError("unsupported engineering context override")
    request={"product":pack["identity"]["name"] if pack["identity"]["group"]=="Product Chiefs" else "",
             "transducer":"Speaker" if pack["identity"]["group"]=="Speaker CoE" else "Microphone" if pack["identity"]["group"]=="Microphone CoE" else "Both",
             "lifecycle":"EVT","risk":risk,"requirement":objective,"required_evidence":["sealed numerical run","independent counterreview"],
             "needed_skills":[skill_id],"available_tools":["FREE_LOCAL_BASELINE"],**(context or {})}
    matrix=factory.matrix(); by_id={r["id"]:r for r in matrix["roles"]}
    if by_id[role_id]["level"] not in {"L2","L3","L4"}: raise ValueError("requested role lacks current execution evidence")
    pod=route_pod(request,matrix)
    if pod["state"]!="PLANNED": raise ValueError("no evaluated capability coverage: "+str(pod["uncovered_skills"]))
    pod["executors"]=[role_id]
    pod["reviewer"]=pack["review_requirements"]["reviewer"]
    pod["evidence_curator"]=pack["review_requirements"]["evidence_curator"]
    seats=list(dict.fromkeys([pod["lead"],role_id,pod["reviewer"],pod["evidence_curator"]]))
    pod["roles"]=[{**by_id[seat],"selection_reason":"Requested contracted executor" if seat==role_id else "Lead / independent review / Evidence curation"} for seat in seats]
    pod["pod_size"]=len(seats)
    store=ControlStore()
    if project_id is None: project_id=store.create_project("AERIS Professional Capability Runs")["id"]
    wf=create_engineering_workflow(objective,role_id,risk=risk,skill_id=skill_id,skill_params=params,description="Structured capability-routed engineering task")
    wf["pod"]=pod
    wf["engineering_context"]={"source_kind":source_kind,"objective":objective,"role_id":role_id,"physical_verification":False}
    _write(wf)
    task=store.create_task(project_id=project_id,title=objective,description=pack["identity"]["name"],risk_level=risk,pod=pod,workflow_id=wf["workflow_id"],metadata={"role_id":role_id,"source_kind":source_kind,"factory_version":catalog.VERSION})
    memory=Harness(); memory.append(project_id,"PROJECT_MEMORY",{"task_id":task["id"],"workflow_id":wf["workflow_id"],"role_id":role_id},role_id)
    try:
        executed=execute_workflow(wf["workflow_id"],role_id)
    except Exception as exc:
        with store._connect() as conn:
            conn.execute("UPDATE tasks SET state=? WHERE id=?",("FAILED_EXECUTION",task["id"]))
        memory.append(project_id,"FAILURE_LIBRARY",{"task_id":task["id"],"error":type(exc).__name__,"skill_id":skill_id},role_id)
        raise
    run_id=executed["execution"]["run_id"]
    if not validate_bundle(run_id)["valid"]: raise ValueError("Evidence failed integrity check")
    with store._connect() as conn:
        conn.execute("UPDATE tasks SET state=?,evidence_ref=? WHERE id=?",(executed["state"],executed["execution"]["evidence_ref"],task["id"]))
    output=executed["execution"]["skill_result"]
    claims=[{"classification":"EVIDENCE","evidence_refs":[run_id],"uncertainty":output["uncertainty"],
             "counter_hypothesis":"Input, fixture or model applicability may explain the result; physical confirmation is outstanding.",
             "source_kind":source_kind,"real_measurement_verified":False}]
    reviewer=pod["reviewer"] if pod["reviewer"]!=role_id else "R006"
    review=catalog.execute("evidence-counterreview",{"executor_role":role_id,"reviewer_role":reviewer,"approved_evidence_refs":[run_id],"claims":claims})
    memory.append(project_id,"SKILL_USAGE",{"skill_id":skill_id,"role_id":role_id,"evidence_run_ids":[run_id]},role_id)
    memory.append(project_id,"EXPERIMENT_MEMORY",{"workflow_id":wf["workflow_id"],"source_kind":source_kind,"evidence_run_ids":[run_id]},role_id)
    memory.append(project_id,"CROSS_ROLE_REVIEW",{"review":review["values"],"evidence_run_ids":[run_id]},reviewer)
    memory.append(project_id,"CONSENSUS_DISAGREEMENT",{"decision":review["values"]["decision"],"unresolved":"physical validity and applicability require independent expert evidence","evidence_run_ids":[run_id]},reviewer)
    memory.append(project_id,"LESSON_MEMORY",{"lesson":"Preserve model assumptions and counter-hypotheses with the run; do not equate synthetic analysis with measurement.","evidence_run_ids":[run_id]},"R099")
    report={"project_id":project_id,"task_id":task["id"],"workflow_id":wf["workflow_id"],"state":executed["state"],"role_id":role_id,
            "pod":pod,"numerical_result":output,"evidence_run_id":run_id,"review":review["values"],"source_kind":source_kind,"human_approval":False}
    factory.write(factory.STATE/"reports"/(wf["workflow_id"]+".json"),report)
    markdown=f"# {objective}\n\nRole: {role_id} — {pack['identity']['name']}\n\nSkill: {skill_id}, version {catalog.VERSION}\n\nSource: {source_kind}; physical validation remains outstanding.\n\nEvidence: {run_id}\n\nWorkflow: {wf['workflow_id']} — {executed['state']}\n\nReview: {review['values']['decision']} by {reviewer}; no Human approval.\n\n## Uncertainty\n\n{output['uncertainty']}\n\n## Counter-hypothesis\n\n{claims[0]['counter_hypothesis']}\n\nNumerical arrays, units, inputs, implementation hashes and reproduction parameters are retained in the sealed Evidence and adjacent JSON report.\n"
    (factory.STATE/"reports"/(wf["workflow_id"]+".md")).write_text(markdown,encoding="utf-8")
    memory.distill(project_id)
    return report
