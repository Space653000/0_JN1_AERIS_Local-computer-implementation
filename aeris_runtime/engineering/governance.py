"""Executable engineering planning, quality and evidence counterchecks."""
from __future__ import annotations

import hashlib
import math
import re

import numpy as np
from scipy import stats

from .numerics import scalar, vector


def requirements(p: dict) -> dict:
    requirements = p["requirements"]
    observations = p["observations"]
    if not isinstance(requirements, list) or not requirements or len(requirements)>1000:
        raise ValueError("nonempty bounded requirement list required")
    ids=[r["id"] for r in requirements]
    if len(set(ids))!=len(ids): raise ValueError("duplicate requirement IDs")
    obs={r["requirement_id"]:r for r in observations}
    if len(obs)!=len(observations) or set(obs)-set(ids): raise ValueError("duplicate or unknown observation requirement")
    checks=[]
    for req in requirements:
        low=scalar(req,"minimum"); high=scalar(req,"maximum")
        if low>high or not req.get("unit"): raise ValueError("invalid requirement bounds/unit")
        item=obs.get(req["id"])
        if item is None:
            checks.append({"id":req["id"],"outcome":"MISSING","reason":"no observation"}); continue
        if item.get("unit")!=req["unit"]: raise ValueError("unit mismatch; implicit conversions forbidden")
        value=scalar(item,"value")
        checks.append({"id":req["id"],"outcome":"PASS" if low<=value<=high else "FAIL",
                       "margin_to_nearest_limit":min(value-low,high-value),"evidence_ref":item.get("evidence_ref"),
                       "evidence_verified":False})
    return {"checks":checks,"coverage":len(obs)/len(requirements),
            "engineering_outcome":"PASS" if all(c["outcome"]=="PASS" for c in checks) else "INCOMPLETE_OR_FAIL",
            "formal_acceptance":False}


def fmea(p: dict) -> dict:
    modes=p["failure_modes"]
    if not isinstance(modes,list) or not modes or len(modes)>1000: raise ValueError("failure modes required")
    result=[]
    for mode in modes:
        ranks=[scalar(mode,k,0,10) for k in ("severity","occurrence","detection")]
        if any(int(x)!=x for x in ranks) or not mode.get("countermeasure") or not mode.get("owner"):
            raise ValueError("integer 1..10 rankings, owner and countermeasure required")
        result.append({**mode,"rpn":math.prod(ranks),"human_review_required":ranks[0]>=9})
    return {"ranked_modes":sorted(result,key=lambda x:(-x["severity"],-x["rpn"],x["id"])),"risk_approval_granted":False}


def process_quality(p: dict) -> dict:
    values=vector(p,"values",5)
    low=scalar(p,"lower_limit"); high=scalar(p,"upper_limit")
    if low>=high or values.std(ddof=1)<=0: raise ValueError("nonzero observed variation and ordered limits required")
    mean=float(values.mean()); sd=float(values.std(ddof=1))
    return {"mean":mean,"sample_sd":sd,"pp":(high-low)/(6*sd),"ppk":min(high-mean,mean-low)/(3*sd),
            "out_of_spec_count":int(sum((values<low)|(values>high))),"normality_p_value":float(stats.shapiro(values[:5000]).pvalue),
            "process_control_proven":False,"assumption":"independent representative observations; Ppk is descriptive, not a stability proof"}


def reliability(p: dict) -> dict:
    n=int(scalar(p,"trials",0,1000000)); failures=int(scalar(p,"failures",-1e-30)); confidence=scalar(p,"confidence",0,.99999)
    if failures>n: raise ValueError("failures exceed trials")
    upper=1.0 if failures==n else float(stats.beta.ppf(confidence,failures+1,n-failures))
    return {"observed_failure_fraction":failures/n,"one_sided_upper_failure_probability":upper,"confidence":confidence,
            "assumption":"independent identical Bernoulli trials; accelerated-life extrapolation not performed"}


def hypotheses(p: dict) -> dict:
    rows=p["hypotheses"]
    if not isinstance(rows,list) or not rows: raise ValueError("hypotheses required")
    findings=[]
    for row in rows:
        if not row.get("discriminating_test") or not row.get("alternative_cause"):
            raise ValueError("every FACA hypothesis needs a discriminating test and counter-hypothesis")
        support=set(row["support_refs"]); refute=set(row["refute_refs"])
        if support & refute: raise ValueError("same evidence classified both support and refutation")
        findings.append({**row,"status":"CONTESTED" if refute else "TEST_REQUIRED",
                         "support_count":len(support),"refutation_count":len(refute),"root_cause_verified":False})
    return {"hypotheses":findings,"next_tests":[r["discriminating_test"] for r in findings]}


def research(p: dict) -> dict:
    query=set(re.findall(r"\w+",p["query"].lower()))
    if not query: raise ValueError("nonempty research query required")
    permitted={"PUBLIC_METADATA","OPEN_ACCESS","USER_OWNED","SYNTHETIC","AERIS_AUTHORED"}
    results=[]
    for doc in p["documents"]:
        if doc["rights"] not in permitted or not doc.get("source"):
            raise ValueError("unknown provenance/rights; paid full text is not accepted")
        content=doc["text"]
        if hashlib.sha256(content.encode()).hexdigest()!=doc["sha256"]: raise ValueError("knowledge document hash mismatch")
        tokens=set(re.findall(r"\w+",(doc["title"]+" "+content).lower()))
        score=len(tokens&query)/len(query)
        if score: results.append({"id":doc["id"],"score":score,"source":doc["source"],"sha256":doc["sha256"],"rights":doc["rights"]})
    return {"matches":sorted(results,key=lambda x:(-x["score"],x["id"])),"search_scope":"supplied local corpus only",
            "legal_novelty_or_freedom_to_operate_opinion":False,"standards_current_edition_verified":False}


def traceability(p: dict) -> dict:
    requirements=set(p["requirement_ids"]); tests=set(p["test_ids"]); links=p["links"]
    if not requirements or not tests or len(requirements)!=len(p["requirement_ids"]) or len(tests)!=len(p["test_ids"]):
        raise ValueError("unique nonempty requirement and test IDs required")
    for link in links:
        if link["requirement_id"] not in requirements or link["test_id"] not in tests: raise ValueError("dangling traceability link")
    covered={r["requirement_id"] for r in links}; missing=sorted(requirements-covered)
    return {"coverage":len(covered)/len(requirements),"missing_requirement_ids":missing,
            "evidence_pending_test_ids":sorted({r["test_id"] for r in links if not r.get("evidence_ref")}),"raw_evidence_changed":False}


def optimize(p: dict) -> dict:
    candidates=np.asarray(p["candidate_points"],dtype=float); observations=p["observations"]
    if candidates.ndim!=2 or not 1<=candidates.shape[1]<=8 or not 1<=len(candidates)<=10000 or not np.isfinite(candidates).all():
        raise ValueError("finite bounded candidate matrix required")
    seen={tuple(r["point"]) for r in observations}
    for row in observations:
        scalar(row,"loss")
        if tuple(row["point"]) not in map(tuple,candidates): raise ValueError("observation outside allowed candidate set")
    remaining=[r for r in candidates if tuple(r) not in seen]
    if len(seen)!=len(observations): raise ValueError("duplicate experiment points")
    if not observations:
        next_point=remaining[0]
    elif remaining:
        span=np.ptp(candidates,axis=0); span[span==0]=1
        next_point=max(remaining,key=lambda x:min(float(np.linalg.norm((x-np.asarray(r["point"]))/span)) for r in observations))
    else: next_point=None
    best=min(observations,key=lambda r:r["loss"]) if observations else None
    return {"next_point":next_point,"best_observed":best,"unexplored_count":len(remaining),
            "policy":"deterministic maximin exploration within supplied safe candidate set","hardware_action_performed":False}


def review(p: dict) -> dict:
    findings=[]
    allowed=set(p["approved_evidence_refs"])
    if p["executor_role"]==p["reviewer_role"]: raise ValueError("executor cannot review its own run")
    for i,claim in enumerate(p["claims"]):
        classification=claim["classification"]
        if classification not in {"EVIDENCE","INFERENCE","HYPOTHESIS","UNKNOWN"}: raise ValueError("unknown claim class")
        refs=set(claim.get("evidence_refs",[]))
        if classification=="EVIDENCE" and (not refs or not refs<=allowed): findings.append({"claim":i,"code":"UNSUPPORTED_EVIDENCE"})
        if not claim.get("uncertainty"): findings.append({"claim":i,"code":"MISSING_UNCERTAINTY"})
        if not claim.get("counter_hypothesis"): findings.append({"claim":i,"code":"MISSING_COUNTER_HYPOTHESIS"})
        if claim.get("source_kind")=="SYNTHETIC" and claim.get("real_measurement_verified"):
            findings.append({"claim":i,"code":"SYNTHETIC_AS_PHYSICAL"})
    return {"findings":findings,"decision":"CHANGES_REQUIRED" if findings else "BASELINE_REVIEW_PASS",
            "reviewer_role":p["reviewer_role"],"independent_human_approval":False}


def product_plan(p: dict) -> dict:
    from .role_specs import product_profile
    index=int(scalar(p,"product_index",-1,23))
    if index!=p["product_index"]: raise ValueError("product index must be integer")
    profile=product_profile(index)
    if p["transducer"] not in {"Speaker","Microphone","Both"} or p["lifecycle"] not in profile["lifecycle"]:
        raise ValueError("unknown transducer/lifecycle")
    if p["risk"] not in {"R0","R1","R2","R3","R4"} or not p["objective"].strip(): raise ValueError("objective and valid risk required")
    report=requirements({"requirements":p["requirements"],"observations":p["observations"]})
    needed=["engineering-requirements","requirement-traceability"]
    if p["transducer"] in {"Speaker","Both"}: needed += ["lumped-speaker","harmonic-noise-analysis"]
    if p["transducer"] in {"Microphone","Both"}: needed += ["microphone-sensitivity","enhancement-aec-metrics"]
    return {"product_index":index,"architecture":profile,"validation_matrix":report["checks"],
            "needed_skills":needed,"requirement_coverage":report["coverage"],
            "task_draft":{"title":p["objective"],"risk":p["risk"],"product_index":index,"lifecycle":p["lifecycle"],"transducer":p["transducer"]},
            "human_release_gate":p["risk"] in {"R3","R4"},"engineering_outcome":report["engineering_outcome"]}


def instrument_sequence(p: dict) -> dict:
    fs=scalar(p,"sample_rate_hz",0,192000); duration=scalar(p,"duration_s",0,60)
    voltage=scalar(p,"requested_rms_v",-1e-30); limit=scalar(p,"safe_rms_limit_v",0)
    if voltage>limit: raise ValueError("requested stimulus exceeds declared voltage safety limit")
    if p["mode"]!="SYNTHETIC_DRY_RUN": raise ValueError("physical IO requires a separately approved driver/session")
    return {"sample_count":int(round(fs*duration)),"voltage_margin_v":limit-voltage,
            "sequence":["validate declared limits","generate deterministic fixture","analyze","seal Evidence","counterreview"],
            "physical_io_performed":False,"instrument_reading_claimed":False}


HANDLERS={"product-system-plan":product_plan,"instrument-sequence":instrument_sequence,"engineering-requirements":requirements,"dfmea-ranking":fmea,"process-quality":process_quality,
          "reliability-binomial":reliability,"failure-hypotheses":hypotheses,"provenance-research":research,
          "requirement-traceability":traceability,"experiment-optimization":optimize,"evidence-counterreview":review}
