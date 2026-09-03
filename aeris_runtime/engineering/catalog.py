"""Versioned executable registry, strict JSON boundaries and analytical evaluation."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import scipy

from . import governance, numerics
from .cases import fixtures

VERSION="1.0.0"
HANDLERS={**numerics.HANDLERS,**governance.HANDLERS}
OPTIONAL={"uncertainty-propagation":{"correlation_matrix":"array"}}


def json_value(value: Any) -> Any:
    if isinstance(value,np.ndarray): return json_value(value.tolist())
    if isinstance(value,np.generic): return json_value(value.item())
    if isinstance(value,dict): return {str(k):json_value(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [json_value(v) for v in value]
    if isinstance(value,float) and not math.isfinite(value): raise ValueError("nonfinite numerical result")
    if value is None or isinstance(value,(str,int,float,bool)): return value
    raise ValueError("unsupported JSON value")


def canonical(value: Any) -> bytes:
    return json.dumps(json_value(value),ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def schema_for(value: Any) -> dict:
    if isinstance(value,bool): return {"type":"boolean"}
    if isinstance(value,(float,int)): return {"type":"number"}
    if isinstance(value,str): return {"type":"string"}
    if value is None: return {"type":["null","number"]}
    if isinstance(value,list):
        return {"type":"array","maxItems":262144,"items":schema_for(value[0]) if value else {}}
    if isinstance(value,dict):
        return {"type":"object","properties":{k:schema_for(v) for k,v in value.items()},"required":list(value),"additionalProperties":False}
    raise ValueError("schema inference requires JSON data")


def validate(value: Any, schema: dict, path="input") -> None:
    kind=schema.get("type")
    if isinstance(kind,list):
        if value is None and "null" in kind: return
        kind=next(k for k in kind if k!="null")
    if kind=="object":
        if not isinstance(value,dict): raise ValueError(f"{path}: object required")
        if set(schema.get("required",[]))-value.keys(): raise ValueError(f"{path}: required fields missing")
        if schema.get("additionalProperties") is False and value.keys()-schema.get("properties",{}).keys(): raise ValueError(f"{path}: unknown fields")
        for k,v in value.items(): validate(v,schema.get("properties",{}).get(k,{}),path+"."+k)
    elif kind=="array":
        if not isinstance(value,list) or len(value)>schema.get("maxItems",262144): raise ValueError(f"{path}: bounded array required")
        for i,v in enumerate(value): validate(v,schema.get("items",{}),f"{path}[{i}]")
    elif kind=="integer":
        if isinstance(value,bool) or not isinstance(value,int): raise ValueError(f"{path}: integer required")
    elif kind=="number":
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value): raise ValueError(f"{path}: finite number required")
    elif kind=="string" and not isinstance(value,str): raise ValueError(f"{path}: string required")
    elif kind=="boolean" and not isinstance(value,bool): raise ValueError(f"{path}: boolean required")


def definitions() -> dict:
    result={}
    for fixture in fixtures():
        skill=fixture["skill_id"]; schema=schema_for(fixture["input"])
        for name in ("product_index","adc_bits","segment_samples","harmonics","trials","seed","fraction","order","failures"):
            if name in schema["properties"]: schema["properties"][name]={"type":"integer"}
        # Dictionaries keyed by experiment factor names are not a single fixed design.
        if skill=="factorial-doe": schema["properties"]["factors"]={"type":"object"}
        # Optional evidence links and full claim fields remain explicitly enumerated.
        if skill=="evidence-counterreview":
            item=schema["properties"]["claims"]["items"]
            item["required"]=["classification"]
            item["properties"].update({"source_kind":{"type":"string"},"real_measurement_verified":{"type":"boolean"}})
        if skill=="requirement-traceability": schema["properties"]["links"]["items"]["required"]=["requirement_id","test_id"]
        for name,kind in OPTIONAL.get(skill,{}).items(): schema["properties"][name]={"type":kind}
        result[skill]={"skill_id":skill,"version":VERSION,"input_schema":schema,"fixture":fixture,
                       "suite":fixture["suite"],"implementation":f"{HANDLERS[skill].__module__}:{HANDLERS[skill].__name__}",
                       "method_reason":fixture["reason"]}
    if set(result)!=set(HANDLERS): raise ValueError("every executable requires an analytical case, and vice versa")
    return result


def _disk_implementation_digest() -> str:
    root=Path(__file__).parent
    files=("numerics.py","governance.py","catalog.py","cases.py","role_specs.py")
    return digest({"sources":{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},"numpy":np.__version__,"scipy":scipy.__version__})


def implementation_digest() -> str:
    if _disk_implementation_digest()!=LOADED_IMPLEMENTATION_SHA256:
        raise RuntimeError("Engineering source changed after module load; restart the capability runtime before execution/evaluation")
    return LOADED_IMPLEMENTATION_SHA256


def execute(skill_id: str, params: dict) -> dict:
    fingerprint=implementation_digest()
    definition=definitions().get(skill_id)
    if definition is None: raise KeyError(skill_id)
    if len(canonical(params))>8_000_000: raise ValueError("input exceeds bounded local workload")
    validate(params,definition["input_schema"])
    values=json_value(HANDLERS[skill_id](copy.deepcopy(params)))
    return {"skill_id":skill_id,"version":VERSION,"result":"PASS","values":values,
            "capability_maturity":"FREE_LOCAL_BASELINE","evidence_class":"DETERMINISTIC_ENGINEERING_CALCULATION",
            "input_sha256":digest(params),"implementation_sha256":fingerprint,
            "uncertainty":"Numerical model only; measurement/calibration uncertainty must be supplied and propagated separately.",
            "professional_tool_verified":False,"physical_measurement_verified":False}


def verify_checks(values: dict, checks: list[dict]) -> list[dict]:
    outcomes=[]
    for rule in checks:
        actual=values
        for part in rule["path"].split("."): actual=actual[int(part)] if isinstance(actual,list) else actual[part]
        reduction=rule.get("reduction")
        if reduction=="length": actual=len(actual)
        elif reduction=="sum": actual=float(np.sum(actual))
        expected=rule["expected"]; tolerance=rule["absolute_tolerance"]
        if reduction=="range": passed=bool(np.all(np.asarray(actual)>=expected[0]) and np.all(np.asarray(actual)<=expected[1]))
        elif isinstance(expected,bool): passed=actual is expected
        elif isinstance(expected,str): passed=actual==expected
        else: passed=bool(np.allclose(actual,expected,atol=tolerance,rtol=0))
        outcomes.append({**rule,"actual":actual,"passed":passed})
    return outcomes


def evaluate(skill_id: str) -> dict:
    definition=definitions()[skill_id]; fixture=definition["fixture"]
    first=execute(skill_id,fixture["input"]); second=execute(skill_id,fixture["input"])
    checks=verify_checks(first["values"],fixture["checks"])
    invalid={**copy.deepcopy(fixture["input"]),**fixture["negative_patch"]}
    rejected=False
    try: execute(skill_id,invalid)
    except (ValueError,KeyError,TypeError): rejected=True
    regression=digest(first)==digest(second)
    return {"skill_id":skill_id,"case_id":fixture["id"],"golden_pass":all(c["passed"] for c in checks),
            "negative_pass":rejected,"regression_pass":regression,"checks":checks,
            "case_sha256":digest(fixture),"output_sha256":digest(first),"implementation_sha256":implementation_digest(),
            "passed":all(c["passed"] for c in checks) and rejected and regression,
            "evaluation_scope":"declared analytical synthetic baseline; not expert/instrument acceptance"}


LOADED_IMPLEMENTATION_SHA256=_disk_implementation_digest()
