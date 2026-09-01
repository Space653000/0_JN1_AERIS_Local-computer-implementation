"""Command-line interface for AERIS portable local-first company runtime."""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from .audit import verify_ledger
from .company import load_company_manifest, validate_company_manifest
from .config import ROOT, load_config, set_persisted_mode
from .corecache import create_snapshot, verify_core_cache
from .evidence import create_bundle, seal_bundle, validate_bundle
from .ingress import approve_quarantined_ingress, download_public_url, public_cloud_query
from .knowledge import build_index, search as knowledge_search, stats as knowledge_stats
from .machine import detect as machine_detect, write_report
from .operations import open_company, serve_supervisor, start_supervisor_background, stop_supervisor, supervisor_status
from .providers import ProviderError
from .review import independent_acceptance
from .router import ModelRouter
from .taskstate import create_task, load_task, transition_task, validate_task
from .verification import gate_summary, record_gate


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_company(args):
    if args.action == "open":
        payload = open_company(actor=args.actor)
        if args.start_supervisor and payload.get("operational_state") != "BLOCKED":
            payload["supervisor"] = start_supervisor_background(args.port)
        _print(payload)
        return 9 if payload.get("operational_state") == "BLOCKED" else 0
    if args.action == "serve":
        return serve_supervisor(args.port, args.heartbeat_interval)
    if args.action == "supervisor-status":
        payload = supervisor_status(args.port)
        _print(payload)
        return 0 if payload.get("reachable") else 10
    if args.action == "stop-supervisor":
        payload = stop_supervisor(args.port)
        _print(payload)
        return 0 if payload.get("stopped") else 10

    status = validate_company_manifest()
    try:
        manifest = load_company_manifest()
        stage = manifest.get("product_stage", "UNKNOWN")
        role_maturity = manifest.get("organization", {}).get("role_maturity", "UNKNOWN")
    except Exception:
        stage = "UNKNOWN"
        role_maturity = "UNKNOWN"
    payload = {
        "company_id": status.company_id,
        "manifest_valid": status.valid,
        "valid": status.valid,
        "product_stage": stage,
        "company_complete": False,
        "virtual_roles": status.role_count,
        "role_maturity": role_maturity,
        "runtime_modes": status.modes,
        "errors": status.errors,
        "supervisor": supervisor_status(),
        "truth": "manifest validity and role registry validity do not mean the AERIS company is complete or production ready",
    }
    _print(payload)
    return 0 if status.valid else 4


def cmd_doctor():
    company = validate_company_manifest()
    try:
        manifest = load_company_manifest()
        product_stage = manifest.get("product_stage", "UNKNOWN")
    except Exception:
        product_stage = "UNKNOWN"
    config = load_config()
    router = ModelRouter(config)
    local_ok, local_detail = router.local.health()
    core_state = ROOT / ".aeris" / "state" / "core-target.json"
    core_cache = ROOT / ".aeris" / "core-reference"
    core_check = verify_core_cache() if core_cache.exists() else {"valid": False, "mode": "missing", "errors": ["Core cache missing"]}
    audit = verify_ledger()
    supervisor = supervisor_status()
    print("AERIS Portable Company Doctor")
    print(f"python: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")
    print(f"product_stage: {product_stage}")
    print(f"company_manifest: {'VALID' if company.valid else 'INVALID'}")
    print("company_complete: NO")
    print(f"virtual_roles: {company.role_count} (capability seats; not 100 verified engineers)")
    print(f"runtime_mode: {config.mode}")
    print(f"local_network_scope: {config.local_network_scope}")
    print("privacy: APPLICATION_PRIVATE_PROVIDER_ENDPOINT_POLICY / PUBLIC_RESEARCH_EXPLICIT")
    print(f"local_provider: {'READY' if local_ok else 'UNAVAILABLE'} — {local_detail}")
    print(f"local_model: {config.local_model}")
    print(f"cloud_configured: {'YES' if config.cloud_configured else 'NO'}")
    print(f"core_cache: {'VERIFIED' if core_check.get('valid') else 'NOT_VERIFIED'} — mode={core_check.get('mode')}")
    print(f"audit_ledger: {'VALID' if audit.get('valid') else 'INVALID'} — records={audit.get('records', 0)}")
    print(f"local_supervisor: {'SERVING' if supervisor.get('reachable') else 'NOT_SERVING'}")
    if core_state.exists():
        try:
            print(f"core_target_sha: {json.loads(core_state.read_text(encoding='utf-8-sig')).get('sha','UNKNOWN')}")
        except Exception:
            print("core_target_sha: STATE_INVALID")
    else:
        print("core_target_sha: BOOTSTRAP_LOCK_OR_SNAPSHOT_ONLY")
    if not company.valid:
        print(f"result: BLOCKED_COMPANY_MANIFEST_INVALID — {company.errors}")
        return 4
    if not audit.get("valid"):
        print("result: BLOCKED_AUDIT_LEDGER_INVALID")
        return 11
    if config.mode in {"offline", "local"} and not local_ok:
        print("result: BLOCKED_LOCAL_CONTINUITY — local/offline mode requires an endpoint-policy-compliant local AI server/model")
        return 2
    if not core_check.get("valid"):
        print("result: KERNEL_RUNTIME_AVAILABLE_CORE_NOT_VERIFIED_NOT_COMPANY_COMPLETE")
        return 0
    if not local_ok:
        print("result: KERNEL_AVAILABLE_WITH_LIMITS_NOT_COMPANY_COMPLETE")
        return 0
    print("result: KERNEL_RUNTIME_READY_NOT_COMPANY_COMPLETE")
    return 0


def cmd_mode(args):
    if args.action == "show":
        print(load_config().mode)
        return 0
    path = set_persisted_mode(args.value)
    print(f"AERIS mode set to {args.value} ({path})")
    return 0


def cmd_chat(args):
    router = ModelRouter(load_config())
    print("[privacy] private engineering chat -> ENDPOINT-POLICY-COMPLIANT LOCAL/TRUSTED-LAN ONLY", file=sys.stderr)
    try:
        result = router.chat(args.text)
    except ProviderError as exc:
        print(f"AERIS provider error: {exc}", file=sys.stderr)
        return 3
    print(f"[{result.provider}:{result.model}]", file=sys.stderr)
    print(result.text)
    return 0


def cmd_research(args):
    try:
        payload = public_cloud_query(args.query)
    except Exception as exc:
        print(f"AERIS public research error: {exc}", file=sys.stderr)
        return 5
    _print(payload)
    return 0


def cmd_ingress(args):
    try:
        payload = download_public_url(args.url, args.max_bytes)
    except Exception as exc:
        print(f"AERIS ingress error: {exc}", file=sys.stderr)
        return 6
    _print(payload)
    return 0


def cmd_ingress_approve(args):
    try:
        payload = approve_quarantined_ingress(args.path, allow_unscanned=args.allow_unscanned, acknowledge_content_risk=args.acknowledge_content_risk)
    except Exception as exc:
        print(f"AERIS ingress approval error: {exc}", file=sys.stderr)
        return 7
    _print(payload)
    return 0


def cmd_knowledge(args):
    if args.action == "build":
        _print(build_index())
        return 0
    if args.action == "stats":
        _print(knowledge_stats())
        return 0
    _print(knowledge_search(args.query, args.limit))
    return 0


def cmd_machine(args):
    report = ROOT / ".aeris" / "state" / "DEPLOYMENT_REPORT.json"
    payload = write_report(report) if args.write else machine_detect()
    _print(payload)
    return 0


def cmd_core(args):
    if args.action == "verify":
        payload = verify_core_cache()
        _print(payload)
        return 0 if payload.get("valid") else 8
    destination = Path(args.output).expanduser()
    payload = create_snapshot(destination)
    _print(payload)
    return 0


def cmd_task(args):
    try:
        if args.action == "create":
            payload = create_task(args.summary, args.actor, task_id=args.task_id, risk=args.risk)
        elif args.action == "show":
            payload = load_task(args.task_id)
            payload["validation_errors"] = validate_task(payload)
        else:
            payload = transition_task(args.task_id, args.state, args.actor, evidence_refs=args.evidence, note=args.note, authority=args.authority)
        _print(payload)
        return 0
    except Exception as exc:
        print(f"AERIS task-state error: {exc}", file=sys.stderr)
        return 12


def cmd_evidence(args):
    try:
        if args.action == "create":
            payload = create_bundle(args.task_id, args.actor, run_id=args.run_id, input_paths=[Path(p) for p in args.input])
        elif args.action == "seal":
            payload = seal_bundle(args.run_id, args.actor)
        else:
            payload = validate_bundle(args.run_id)
        _print(payload)
        return 0 if payload.get("valid", True) else 13
    except Exception as exc:
        print(f"AERIS evidence error: {exc}", file=sys.stderr)
        return 13


def cmd_verify(args):
    try:
        if args.action == "summary":
            payload = gate_summary(args.task_id)
        else:
            payload = record_gate(args.task_id, args.gate, args.outcome, args.reviewer, evidence_refs=args.evidence, note=args.note, reviewer_role=args.reviewer_role)
        _print(payload)
        return 0
    except Exception as exc:
        print(f"AERIS verification error: {exc}", file=sys.stderr)
        return 14


def cmd_audit(args):
    payload = verify_ledger()
    _print(payload)
    return 0 if payload.get("valid") else 15


def cmd_review(args):
    payload = independent_acceptance(args.reviewer)
    _print(payload)
    return 0 if payload.get("final_result") in {"PASS", "PASS_WITH_LIMITS"} else 16


def build_parser():
    p = argparse.ArgumentParser(prog="aeris", description="AERIS portable local-first company runtime")
    s = p.add_subparsers(dest="command", required=True)
    s.add_parser("doctor")

    c = s.add_parser("company")
    cs = c.add_subparsers(dest="action", required=True)
    cs.add_parser("status")
    co = cs.add_parser("open")
    co.add_argument("--actor", default="Codex Autopilot")
    co.add_argument("--start-supervisor", action="store_true")
    co.add_argument("--port", type=int, default=8765)
    cv = cs.add_parser("serve")
    cv.add_argument("--port", type=int, default=8765)
    cv.add_argument("--heartbeat-interval", type=int, default=30)
    cst = cs.add_parser("supervisor-status")
    cst.add_argument("--port", type=int, default=8765)
    csp = cs.add_parser("stop-supervisor")
    csp.add_argument("--port", type=int, default=8765)

    m = s.add_parser("mode")
    ms = m.add_subparsers(dest="action", required=True)
    ms.add_parser("show")
    mm = ms.add_parser("set")
    mm.add_argument("value", choices=["offline", "local", "cloud", "auto"])

    ch = s.add_parser("chat", help="Private engineering chat; endpoint-policy-compliant local/trusted-LAN provider only")
    ch.add_argument("text")
    r = s.add_parser("research", help="Public cloud research only; no local context egress")
    r.add_argument("query")

    i = s.add_parser("ingress", help="Download public URL into local quarantine")
    i.add_argument("url")
    i.add_argument("--max-bytes", type=int, default=50_000_000)
    ia = s.add_parser("ingress-approve", help="Human promotion of a quarantined public ingress artifact")
    ia.add_argument("path")
    ia.add_argument("--allow-unscanned", action="store_true")
    ia.add_argument("--acknowledge-content-risk", action="store_true")

    k = s.add_parser("knowledge")
    ks = k.add_subparsers(dest="action", required=True)
    ks.add_parser("build")
    ks.add_parser("stats")
    kq = ks.add_parser("search")
    kq.add_argument("query")
    kq.add_argument("--limit", type=int, default=10)

    ma = s.add_parser("machine")
    mas = ma.add_subparsers(dest="action", required=True)
    md = mas.add_parser("detect")
    md.add_argument("--write", action="store_true")

    core = s.add_parser("core", help="Verify or snapshot the read-only canonical Core cache")
    cores = core.add_subparsers(dest="action", required=True)
    cores.add_parser("verify")
    snap = cores.add_parser("snapshot")
    snap.add_argument("--output", default="portable_assets/core-reference")

    task = s.add_parser("task", help="Engineering task identity/state machine")
    tasks = task.add_subparsers(dest="action", required=True)
    tc = tasks.add_parser("create")
    tc.add_argument("summary")
    tc.add_argument("--actor", required=True)
    tc.add_argument("--task-id")
    tc.add_argument("--risk", default="R0")
    ts = tasks.add_parser("show")
    ts.add_argument("task_id")
    tt = tasks.add_parser("transition")
    tt.add_argument("task_id")
    tt.add_argument("state")
    tt.add_argument("--actor", required=True)
    tt.add_argument("--authority", default="")
    tt.add_argument("--evidence", action="append", default=[])
    tt.add_argument("--note", default="")

    ev = s.add_parser("evidence", help="Evidence Bundle baseline")
    evs = ev.add_subparsers(dest="action", required=True)
    ec = evs.add_parser("create")
    ec.add_argument("task_id")
    ec.add_argument("--actor", required=True)
    ec.add_argument("--run-id")
    ec.add_argument("--input", action="append", default=[])
    es = evs.add_parser("seal")
    es.add_argument("run_id")
    es.add_argument("--actor", required=True)
    evv = evs.add_parser("verify")
    evv.add_argument("run_id")

    vg = s.add_parser("verify", help="G0-G5 structured gate records")
    vgs = vg.add_subparsers(dest="action", required=True)
    vr = vgs.add_parser("record")
    vr.add_argument("task_id")
    vr.add_argument("gate")
    vr.add_argument("outcome", choices=["PASS", "FAIL", "BLOCKED"])
    vr.add_argument("--reviewer", required=True)
    vr.add_argument("--reviewer-role", default="")
    vr.add_argument("--evidence", action="append", default=[])
    vr.add_argument("--note", default="")
    vs = vgs.add_parser("summary")
    vs.add_argument("task_id")

    au = s.add_parser("audit")
    aus = au.add_subparsers(dest="action", required=True)
    aus.add_parser("verify")

    rv = s.add_parser("review", help="Generate deterministic independent-review evidence for Claude")
    rv.add_argument("--reviewer", default="Claude Code")
    return p


def main():
    a = build_parser().parse_args()
    if a.command == "doctor":
        return cmd_doctor()
    if a.command == "company":
        return cmd_company(a)
    if a.command == "mode":
        return cmd_mode(a)
    if a.command == "chat":
        return cmd_chat(a)
    if a.command == "research":
        return cmd_research(a)
    if a.command == "ingress":
        return cmd_ingress(a)
    if a.command == "ingress-approve":
        return cmd_ingress_approve(a)
    if a.command == "knowledge":
        return cmd_knowledge(a)
    if a.command == "machine":
        return cmd_machine(a)
    if a.command == "core":
        return cmd_core(a)
    if a.command == "task":
        return cmd_task(a)
    if a.command == "evidence":
        return cmd_evidence(a)
    if a.command == "verify":
        return cmd_verify(a)
    if a.command == "audit":
        return cmd_audit(a)
    if a.command == "review":
        return cmd_review(a)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
