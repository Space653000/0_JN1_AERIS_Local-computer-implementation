"""Local-AI intake proposes methods; deterministic contracts control execution."""
from __future__ import annotations

import json
import re

from ..config import load_config
from ..router import ModelRouter
from . import catalog
from .harness import Harness
from .orchestration import route_pod


def understand(description: str, *, product="",transducer="Both",lifecycle="EVT",project="CAPABILITY_FACTORY",router=None):
    if not isinstance(description,str) or not 1<=len(description.strip())<=20000: raise ValueError("bounded engineering description required")
    definitions=catalog.definitions()
    index={skill:{"purpose":d["method_reason"],"required_inputs":d["input_schema"]["required"]} for skill,d in definitions.items()}
    prompt=("You are AERIS local engineering intake. Return ONLY JSON with keys objective (string), needed_skills (list of 1 to 4 exact IDs), "
            "hypotheses (list of strings). Select only methods whose applicability fits the supplied question. Do not invent numerical inputs, measurements, standards, tool runs or approvals. "
            "No shell commands or paths. These are free analytical baselines, not professional instrument verification. Available methods: "+json.dumps(index,ensure_ascii=False))
    if router is None:
        config=load_config()
        if config.local_network_scope!="loopback": raise ValueError("Professional Factory intake requires a loopback local AI endpoint")
        router=ModelRouter(config)
    response=router.chat(description,prompt)
    text=response.text.strip()
    match=re.fullmatch(r"```(?:json)?\s*(.*?)\s*```",text,re.S)
    if match: text=match[1]
    proposal=json.loads(text)
    if not isinstance(proposal,dict) or set(proposal)!={"objective","needed_skills","hypotheses"}:
        raise ValueError("local AI proposal failed strict schema; nothing executed")
    if not isinstance(proposal["objective"],str) or not proposal["objective"].strip() or not isinstance(proposal["needed_skills"],list) or not 1<=len(proposal["needed_skills"])<=4:
        raise ValueError("local AI objective/skill proposal invalid")
    if any(not isinstance(s,str) or s not in definitions for s in proposal["needed_skills"]) or not isinstance(proposal["hypotheses"],list) or any(not isinstance(s,str) for s in proposal["hypotheses"]):
        raise ValueError("unknown skill or malformed hypotheses; nothing executed")
    request={"product":product,"transducer":transducer,"lifecycle":lifecycle,"risk":"R1","requirement":description,
             "required_evidence":["input dataset provenance","sealed local numerical calculation","counterreview"],
             "needed_skills":proposal["needed_skills"],"available_tools":["FREE_LOCAL_BASELINE"]}
    pod=route_pod(request)
    missing={s:definitions[s]["input_schema"]["required"] for s in proposal["needed_skills"]}
    result={"proposal":proposal,"pod":pod,"required_input_fields":missing,"provider":response.provider,"model":response.model,
            "classification":"INFERENCE","numerical_inputs_invented":False,"execution_performed":False,"memory_is_evidence":False}
    Harness().append(project,"HOT_CONTEXT",result,"AERIS Local AI Intake")
    return result
