"""AERIS engineering workflow baseline.

Connects task identity, Dynamic Pod planning, deterministic Skills, Evidence Bundle,
and G0/G1 verification without bypassing domain/independent/Human gates. Versioned
workflow templates provide repeatable starting contracts; template existence never
counts as an executed or verified workflow run.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import append_event
from .config import ROOT
from .evidence import bundle_dir, create_bundle, seal_bundle, validate_bundle
from .roles import plan_pod
from .skills_runtime import list_skills, run_skill
from .taskstate import create_task, load_task, transition_task
from .verification import gate_summary, record_gate

WORKFLOW_ROOT = ROOT / ".aeris" / "workflows"
TEMPLATES_PATH = ROOT / "workflows" / "templates.v1.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in value.strip())
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("invalid workflow id")
    return cleaned[:140]


def workflow_path(workflow_id: str) -> Path:
    return WORKFLOW_ROOT / (_safe_id(workflow_id) + ".json")


def _write(payload: dict[str, Any]) -> dict[str, Any]:
    path = workflow_path(str(payload["workflow_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["updated_at_utc"] = _now()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return payload


def _template_document() -> dict[str, Any]:
    if not TEMPLATES_PATH.exists():
        return {"schema_version": 1, "templates": []}
    data = json.loads(TEMPLATES_PATH.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1 or not isinstance(data.get("templates"), list):
        raise ValueError("unsupported workflow template registry")
    return data


def list_workflow_templates() -> list[dict[str, Any]]:
    templates = _template_document().get("templates", [])
    known_skills = {str(item.get("skill_id")) for item in list_skills()}
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in templates:
        if not isinstance(raw, dict):
            raise ValueError("workflow template must be an object")
        item = dict(raw)
        template_id = _safe_id(str(item.get("template_id", "")))
        if template_id in seen:
            raise ValueError(f"duplicate workflow template_id: {template_id}")
        seen.add(template_id)
        skill_id = str(item.get("skill_id", "")).strip()
        if skill_id not in known_skills:
            raise ValueError(f"workflow template {template_id} references unknown skill: {skill_id}")
        required = item.get("required_inputs", [])
        if not isinstance(required, list) or any(not isinstance(x, str) or not x.strip() for x in required):
            raise ValueError(f"workflow template {template_id} required_inputs invalid")
        item["template_id"] = template_id
        item["execution_state"] = "EXECUTABLE_TEMPLATE_NOT_RUN"
        result.append(item)
    return result


def get_workflow_template(template_id: str) -> dict[str, Any]:
    normalized = _safe_id(template_id)
    for item in list_workflow_templates():
        if item["template_id"] == normalized:
            return item
    raise KeyError(template_id)


def load_workflow(workflow_id: str) -> dict[str, Any]:
    return json.loads(workflow_path(workflow_id).read_text(encoding="utf-8-sig"))


def list_workflows(limit: int = 100) -> list[dict[str, Any]]:
    if not WORKFLOW_ROOT.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(WORKFLOW_ROOT.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[: max(1, min(int(limit), 500))]:
        try:
            result.append(json.loads(path.read_text(encoding="utf-8-sig")))
        except Exception:
            continue
    return result


def create_engineering_workflow(
    summary: str,
    actor: str,
    *,
    description: str = "",
    risk: str = "R0",
    skill_id: str | None = None,
    skill_params: dict[str, Any] | None = None,
    max_roles: int = 8,
    template_id: str | None = None,
) -> dict[str, Any]:
    summary = summary.strip()
    if not summary:
        raise ValueError("summary is required")
    query = (description or summary).strip()
    pod = plan_pod(query, max_roles=max_roles)
    task = create_task(summary, actor, risk=risk, metadata={"description": description, "pod": pod, "workflow_template_id": template_id})
    wid = _safe_id("WF-" + uuid.uuid4().hex[:12].upper())
    payload = {
        "schema_version": 1,
        "workflow_id": wid,
        "workflow_template_id": template_id,
        "task_id": task["task_id"],
        "summary": summary,
        "description": description,
        "risk": risk,
        "created_by": actor,
        "created_at_utc": _now(),
        "state": "DRAFT",
        "pod": pod,
        "execution": {
            "skill_id": skill_id,
            "skill_params": skill_params or {},
            "skill_result": None,
            "run_id": None,
        },
        "verification": gate_summary(task["task_id"]),
        "next_gate": "READY_FOR_EXECUTION",
        "truth": "Workflow automation may complete deterministic execution/evidence/G0-G1 only. G2 domain, G3 regression, G4 independent review and G5 Human approval remain explicit gates.",
    }
    _write(payload)
    append_event("WORKFLOW_CREATED", actor, {"workflow_id": wid, "template_id": template_id, "task_id": task["task_id"], "skill_id": skill_id, "pod_size": pod["pod_size"]})
    return payload


def create_workflow_from_template(
    template_id: str,
    actor: str,
    *,
    summary: str = "",
    description: str = "",
    skill_params: dict[str, Any] | None = None,
    max_roles: int = 8,
) -> dict[str, Any]:
    template = get_workflow_template(template_id)
    params = dict(skill_params or {})
    missing = [
        name
        for name in template.get("required_inputs", [])
        if name not in params or params[name] is None or params[name] == ""
    ]
    if missing:
        raise ValueError(f"workflow template missing required inputs: {', '.join(missing)}")
    effective_summary = summary.strip() or str(template.get("name", template_id))
    return create_engineering_workflow(
        effective_summary,
        actor,
        description=description,
        risk=str(template.get("default_risk", "R0")),
        skill_id=str(template["skill_id"]),
        skill_params=params,
        max_roles=max_roles,
        template_id=str(template["template_id"]),
    )


def execute_workflow(workflow_id: str, actor: str) -> dict[str, Any]:
    wf = load_workflow(workflow_id)
    task_id = str(wf["task_id"])
    task = load_task(task_id)
    if task["state"] == "DRAFT":
        transition_task(task_id, "READY", actor, note="workflow contract accepted for deterministic baseline")
        task = load_task(task_id)
    if task["state"] == "READY":
        transition_task(task_id, "EXECUTING", actor)
    elif task["state"] != "EXECUTING":
        raise ValueError(f"workflow cannot execute from task state {task['state']}")

    skill_id = wf.get("execution", {}).get("skill_id")
    params = dict(wf.get("execution", {}).get("skill_params") or {})
    if not skill_id:
        transition_task(task_id, "BLOCKED", actor, note="No deterministic Skill configured")
        wf["state"] = "BLOCKED"
        wf["next_gate"] = "SELECT_SKILL"
        return _write(wf)

    try:
        result = run_skill(str(skill_id), params)
    except Exception as exc:
        transition_task(task_id, "FAILED_EXECUTION", actor, note=f"{type(exc).__name__}: {exc}")
        wf["state"] = "FAILED_EXECUTION"
        wf["execution"]["error"] = {"type": type(exc).__name__, "detail": str(exc)}
        _write(wf)
        raise

    transition_task(task_id, "EXECUTED", actor)
    input_paths: list[Path] = []
    if params.get("input_path"):
        input_paths.append(Path(str(params["input_path"])))
    method_snapshot = {
        "skill_id": skill_id,
        "executor": "aeris_runtime.skills_runtime",
        "parameters": {k: v for k, v in params.items() if k != "input_path"},
    }
    requirement_snapshot = params.get("requirement") if isinstance(params.get("requirement"), dict) else {}
    bundle = create_bundle(
        task_id,
        actor,
        input_paths=input_paths,
        requirement_snapshot=requirement_snapshot,
        method_snapshot=method_snapshot,
    )
    run_id = str(bundle["run_id"])
    root = bundle_dir(run_id)
    (root / "processed" / "skill_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result.get("capability_maturity") == "FREE_LOCAL_BASELINE":
        from .engineering.reporting import write_artifacts
        write_artifacts(root,params,result,wf.get("engineering_context"))
    validation = {
        "state": "DETERMINISTIC_SKILL_EXECUTED",
        "skill_id": skill_id,
        "skill_result": result.get("result", "UNKNOWN"),
        "checks": result.get("checks", []),
        "truth": "This validates the deterministic Skill result only; domain and independent verification remain separate gates.",
    }
    (root / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    seal_bundle(run_id, actor)
    integrity = validate_bundle(run_id)
    if not integrity.get("valid"):
        transition_task(task_id, "FAILED_EVIDENCE", actor, evidence_refs=[str(root)], note="Evidence Bundle integrity failed after seal")
        wf["state"] = "FAILED_EVIDENCE"
        wf["execution"].update({"skill_result": result, "run_id": run_id})
        return _write(wf)

    evidence_ref = str(root)
    transition_task(task_id, "EVIDENCED", actor, evidence_refs=[evidence_ref])
    record_gate(task_id, "G0_CONTRACT", "PASS", actor, evidence_refs=[evidence_ref], note="Workflow/Skill contract and immutable input snapshot baseline present")
    numerical = str(result.get("evidence_class", "")).startswith("DETERMINISTIC_")
    if numerical and result.get("result") in {"PASS", "FAIL"}:
        outcome = "PASS" if result.get("result") == "PASS" else "FAIL"
        record_gate(task_id, "G1_NUMERICAL", outcome, actor, evidence_refs=[evidence_ref], note="Deterministic Skill numerical/validation result")

    wf["state"] = "EVIDENCED"
    wf["execution"].update({"skill_result": result, "run_id": run_id, "evidence_ref": evidence_ref})
    wf["verification"] = gate_summary(task_id)
    wf["next_gate"] = "G2_DOMAIN_REVIEW"
    _write(wf)
    append_event("WORKFLOW_EXECUTED_EVIDENCED", actor, {"workflow_id": workflow_id, "task_id": task_id, "run_id": run_id, "skill_id": skill_id, "skill_result": result.get("result")})
    return wf


def record_review_gate(
    workflow_id: str,
    gate: str,
    outcome: str,
    reviewer: str,
    *,
    reviewer_role: str = "",
    evidence_refs: list[str] | None = None,
    note: str = "",
) -> dict[str, Any]:
    wf = load_workflow(workflow_id)
    task_id = str(wf["task_id"])
    record_gate(task_id, gate, outcome, reviewer, reviewer_role=reviewer_role, evidence_refs=evidence_refs or [], note=note)
    summary = gate_summary(task_id)
    wf["verification"] = summary
    if summary["g0_g4_passed"]:
        task = load_task(task_id)
        if task["state"] == "EVIDENCED":
            refs = [str(x) for x in (evidence_refs or []) if str(x).strip()]
            if not refs and wf.get("execution", {}).get("evidence_ref"):
                refs = [str(wf["execution"]["evidence_ref"])]
            transition_task(task_id, "VERIFIED", reviewer, authority=reviewer, evidence_refs=refs, note="G0-G4 passed")
        wf["state"] = "VERIFIED"
        wf["next_gate"] = "G5_HUMAN_APPROVAL"
    _write(wf)
    return wf
