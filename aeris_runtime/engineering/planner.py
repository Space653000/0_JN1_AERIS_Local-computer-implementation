"""Bounded multi-step sequential execution.

Everything that existed before this module could only decide WHAT to run
once (`intake.understand`, a single LLM call proposing 1-4 skills) or
assign roles to an already-decided skill list (`orchestration.route_pod`).
Nothing could execute one real skill, look at its actual result, and let
that inform which skill runs next. This module adds exactly that -- and
nothing else. It composes `intake.understand`/`orchestration.route_pod`/
`orchestration.run_role` exactly as they exist; it adds no new risk path,
no new review mechanism, and no new authority-grant path of its own.

Risk stays fixed for the whole run and is never present in the per-step
decision JSON, so the local model choosing the next skill has no field
through which it could ever raise risk -- `run_role`/`route_pod` already
hard-block anything outside R0/R1 unconditionally, and this module relies
on that existing block rather than re-implementing it.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone

from ..audit import append_event
from ..config import ROOT, load_config
from ..router import ModelRouter
from . import catalog, factory
from .intake import understand
from .orchestration import route_pod, run_role

PLAN_EVIDENCE_DIR = ROOT / ".aeris" / "evidence" / "plans"
_ABSOLUTE_MAX_STEPS = 8
_MAX_VALUES_CHARS_IN_PROMPT = 2000

_STEP_DECISION_KEYS = {"decision", "next_skill_id", "reason"}


def _step_summary_for_prompt(report: dict) -> dict:
    """Bound what one step's real result contributes to the next prompt.

    Some catalog skills return full sample arrays; dumping several of
    those into an already-bounded local model's context would either
    truncate silently or crowd out the objective. A digest still lets the
    model reason about "did step 1 produce something," it just can't see
    the raw numbers -- the full values remain in the returned trace and
    in the sealed Evidence referenced by evidence_run_id.
    """
    values = report["numerical_result"]["values"]
    encoded = json.dumps(catalog.json_value(values), ensure_ascii=False, sort_keys=True)
    if len(encoded) <= _MAX_VALUES_CHARS_IN_PROMPT:
        values_view = values
    else:
        values_view = {
            "values_sha256": catalog.digest(values),
            "note": "full numerical result omitted from prompt (exceeds size bound); see evidence_run_id",
        }
    return {
        "skill_id": report["numerical_result"]["skill_id"],
        "state": report["state"],
        "values": values_view,
        "evidence_run_id": report["evidence_run_id"],
    }


def _step_decision_prompt(candidates: dict) -> str:
    return (
        "You are AERIS local sequential engineering planner. One or more real steps already ran; decide "
        "only whether a further real step is justified by their actual results. Return ONLY JSON with keys "
        "decision ('CONTINUE' or 'STOP'), next_skill_id (exact catalog ID when decision is CONTINUE, else "
        "null), reason (string). Continue only when the objective and the steps already run give a concrete, "
        "evidence-based reason a further method would add real information; when unsure, stop. Never propose "
        "a skill_id that already appears in the steps already run. Do not invent numerical inputs, "
        "measurements, standards, tool runs or approvals -- you are choosing the next method, not supplying "
        "its parameters. No shell commands or paths. These are free analytical baselines, not professional "
        "instrument verification. Available next methods: " + json.dumps(candidates, ensure_ascii=False)
    )


def _parse_step_decision(text: str, definitions: dict) -> dict:
    """Strict single-JSON-object validation, the same idiom
    intake.understand() uses -- but unlike intake.py, this explicitly
    catches JSONDecodeError so a malformed model reply stops the plan
    closed instead of propagating an uncaught exception.
    """
    text = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
    if match:
        text = match[1]
    try:
        decision = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("planner decision failed strict schema; nothing further executed") from exc
    if not isinstance(decision, dict) or set(decision) != _STEP_DECISION_KEYS:
        raise ValueError("planner decision failed strict schema; nothing further executed")
    if decision["decision"] not in {"CONTINUE", "STOP"}:
        raise ValueError("planner decision failed strict schema; nothing further executed")
    if not isinstance(decision["reason"], str) or not decision["reason"].strip():
        raise ValueError("planner decision failed strict schema; nothing further executed")
    next_skill = decision["next_skill_id"]
    if decision["decision"] == "STOP":
        if next_skill is not None:
            raise ValueError("planner decision failed strict schema; nothing further executed")
    elif not isinstance(next_skill, str) or next_skill not in definitions:
        raise ValueError("planner decision failed strict schema; nothing further executed")
    return decision


def plan_and_execute(
    objective: str,
    *,
    available_params: dict,
    risk: str = "R0",
    transducer: str = "Both",
    lifecycle: str = "EVT",
    product: str = "",
    project_id: str | None = None,
    initial_skill_id: str | None = None,
    source_kind: str = "USER_SUPPLIED_UNVERIFIED",
    max_steps: int = 5,
    router=None,
) -> dict:
    if risk not in {"R0", "R1"}:
        raise ValueError("planner only permits R0/R1 automatic execution; higher-risk approval must be explicit")
    if source_kind not in {"SYNTHETIC", "USER_SUPPLIED_UNVERIFIED"}:
        raise ValueError("cannot self-assert calibrated/verified data")
    if not isinstance(max_steps, int) or not 1 <= max_steps <= _ABSOLUTE_MAX_STEPS:
        raise ValueError(f"max_steps must be an int in 1..{_ABSOLUTE_MAX_STEPS}")
    if not isinstance(available_params, dict):
        raise ValueError("available_params must be a dict of {skill_id: params}")
    if not isinstance(objective, str) or not 1 <= len(objective.strip()) <= 20000:
        raise ValueError("bounded engineering objective required")

    definitions = catalog.definitions()

    if router is None:
        config = load_config()
        if config.local_network_scope != "loopback":
            raise ValueError("planner requires a loopback local AI endpoint")
        router = ModelRouter(config)

    if initial_skill_id is not None:
        if initial_skill_id not in definitions:
            raise ValueError(f"unknown initial_skill_id: {initial_skill_id}")
        candidate = initial_skill_id
    else:
        proposal = understand(objective, product=product, transducer=transducer, lifecycle=lifecycle, router=router)
        candidate = proposal["proposal"]["needed_skills"][0]

    matrix = factory.matrix()
    steps: list[dict] = []
    decisions: list[dict] = []
    executed_skill_ids: set[str] = set()
    stop_reason = "max_steps_reached"

    for _ in range(max_steps):
        required = definitions[candidate]["input_schema"]["required"]
        params = available_params.get(candidate)
        if params is None or set(required) - set(params):
            stop_reason = f"missing_required_input:{candidate}"
            break

        pod = route_pod({
            "needed_skills": [candidate], "risk": risk, "transducer": transducer, "lifecycle": lifecycle,
            "product": product, "requirement": objective,
            "required_evidence": ["sealed numerical run", "counterreview"],
            "available_tools": ["FREE_LOCAL_BASELINE"],
        }, matrix)
        if not pod["executors"]:
            stop_reason = f"no_qualified_role:{candidate}"
            break

        report = run_role(
            pod["executors"][0], candidate, params, objective=objective, project_id=project_id,
            risk=risk, source_kind=source_kind,
            context={"product": product, "transducer": transducer, "lifecycle": lifecycle},
        )
        project_id = report["project_id"]
        steps.append(report)
        executed_skill_ids.add(candidate)

        if report["state"] != "EVIDENCED":
            stop_reason = f"step_failed:{report['state']}"
            break
        if len(steps) == max_steps:
            stop_reason = "max_steps_reached"
            break

        candidates = {
            skill: {"purpose": data["method_reason"], "required_inputs": data["input_schema"]["required"]}
            for skill, data in definitions.items() if skill not in executed_skill_ids
        }
        trace_summary = [_step_summary_for_prompt(r) for r in steps]
        response = router.chat(
            json.dumps({"objective": objective, "steps_already_run": trace_summary}, ensure_ascii=False),
            _step_decision_prompt(candidates),
        )
        try:
            decision = _parse_step_decision(response.text, definitions)
        except ValueError:
            stop_reason = "planner_decision_invalid"
            break
        decisions.append(decision)

        if decision["decision"] == "STOP":
            stop_reason = "planner_stopped"
            break
        if decision["next_skill_id"] in executed_skill_ids:
            stop_reason = "repeated_skill_no_progress"
            break
        candidate = decision["next_skill_id"]

    plan_id = "PLAN-" + uuid.uuid4().hex
    PLAN_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (PLAN_EVIDENCE_DIR / f"{plan_id}.json").write_text(json.dumps({
        "schema_version": 1, "plan_id": plan_id, "objective": objective, "risk": risk,
        "transducer": transducer, "lifecycle": lifecycle, "product": product, "project_id": project_id,
        "steps": steps, "decisions": decisions, "stop_reason": stop_reason,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    append_event("PLAN_EXECUTED", "AERIS Planner", {
        "plan_id": plan_id, "objective": objective, "step_count": len(steps), "stop_reason": stop_reason,
        "step_skill_ids": [s["numerical_result"]["skill_id"] for s in steps],
    })

    return {
        "plan_id": plan_id, "objective": objective, "project_id": project_id,
        "steps": steps, "decisions": decisions, "stop_reason": stop_reason,
    }
