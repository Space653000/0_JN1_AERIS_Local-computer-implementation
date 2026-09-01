"""Command-line interface for AERIS portable company runtime."""
from __future__ import annotations
import argparse, json, platform, sys
from .company import validate_company_manifest
from .config import ROOT, load_config, set_persisted_mode
from .providers import ProviderError
from .router import ModelRouter
from .knowledge import build_index, search as knowledge_search, stats as knowledge_stats
from .machine import detect as machine_detect, write_report
from .ingress import public_cloud_query, download_public_url, approve_quarantined_ingress


def cmd_company(args):
    status=validate_company_manifest(); payload={"company_id":status.company_id,"valid":status.valid,"virtual_roles":status.role_count,"runtime_modes":status.modes,"errors":status.errors}; print(json.dumps(payload,ensure_ascii=False,indent=2)); return 0 if status.valid else 4

def cmd_doctor():
    company=validate_company_manifest(); config=load_config(); router=ModelRouter(config); local_ok,local_detail=router.local.health(); core_state=ROOT/".aeris"/"state"/"core-target.json"; core_cache=ROOT/".aeris"/"core-reference"
    print("AERIS Portable Company Doctor"); print(f"python: {sys.version.split()[0]}"); print(f"platform: {platform.platform()}"); print(f"company_manifest: {'VALID' if company.valid else 'INVALID'}"); print(f"virtual_roles: {company.role_count}"); print(f"runtime_mode: {config.mode}"); print("privacy: APPLICATION_LEVEL_PRIVATE_ENGINEERING_LOCAL_ONLY / PUBLIC_RESEARCH_EXPLICIT"); print(f"local_provider: {'READY' if local_ok else 'UNAVAILABLE'} — {local_detail}"); print(f"local_model: {config.local_model}"); print(f"cloud_configured: {'YES' if config.cloud_configured else 'NO'}"); print(f"core_cache: {'PRESENT' if core_cache.exists() else 'NOT_CACHED'}")
    if core_state.exists():
        try: print(f"core_target_sha: {json.loads(core_state.read_text(encoding='utf-8')).get('sha','UNKNOWN')}")
        except Exception: print("core_target_sha: STATE_INVALID")
    else: print("core_target_sha: BOOTSTRAP_LOCK_ONLY")
    if not company.valid: print(f"result: BLOCKED — company manifest invalid: {company.errors}"); return 4
    if config.mode in {"offline","local"} and not local_ok: print("result: BLOCKED — local/offline mode requires a reachable local AI server/model"); return 2
    print("result: READY_WITH_LIMITS" if not local_ok else "result: READY"); return 0

def cmd_mode(args):
    if args.action=="show": print(load_config().mode); return 0
    path=set_persisted_mode(args.value); print(f"AERIS mode set to {args.value} ({path})"); return 0

def cmd_chat(args):
    router=ModelRouter(load_config()); print("[privacy] private engineering chat -> LOCAL ONLY",file=sys.stderr)
    try: result=router.chat(args.text)
    except ProviderError as exc: print(f"AERIS provider error: {exc}",file=sys.stderr); return 3
    print(f"[{result.provider}:{result.model}]",file=sys.stderr); print(result.text); return 0

def cmd_research(args):
    try: payload=public_cloud_query(args.query)
    except Exception as exc: print(f"AERIS public research error: {exc}",file=sys.stderr); return 5
    print(json.dumps(payload,ensure_ascii=False,indent=2)); return 0

def cmd_ingress(args):
    try: payload=download_public_url(args.url,args.max_bytes)
    except Exception as exc: print(f"AERIS ingress error: {exc}",file=sys.stderr); return 6
    print(json.dumps(payload,ensure_ascii=False,indent=2)); return 0

def cmd_ingress_approve(args):
    try:
        payload=approve_quarantined_ingress(args.path,allow_unscanned=args.allow_unscanned,acknowledge_content_risk=args.acknowledge_content_risk)
    except Exception as exc:
        print(f"AERIS ingress approval error: {exc}",file=sys.stderr); return 7
    print(json.dumps(payload,ensure_ascii=False,indent=2)); return 0

def cmd_knowledge(args):
    if args.action=="build": print(json.dumps(build_index(),ensure_ascii=False,indent=2)); return 0
    if args.action=="stats": print(json.dumps(knowledge_stats(),ensure_ascii=False,indent=2)); return 0
    print(json.dumps(knowledge_search(args.query,args.limit),ensure_ascii=False,indent=2)); return 0

def cmd_machine(args):
    report=ROOT/".aeris"/"state"/"DEPLOYMENT_REPORT.json"; payload=write_report(report) if args.write else machine_detect(); print(json.dumps(payload,ensure_ascii=False,indent=2)); return 0

def build_parser():
    p=argparse.ArgumentParser(prog="aeris",description="AERIS portable local-first company runtime"); s=p.add_subparsers(dest="command",required=True)
    s.add_parser("doctor"); c=s.add_parser("company"); cs=c.add_subparsers(dest="action",required=True); cs.add_parser("status")
    m=s.add_parser("mode"); ms=m.add_subparsers(dest="action",required=True); ms.add_parser("show"); mm=ms.add_parser("set"); mm.add_argument("value",choices=["offline","local","cloud","auto"])
    ch=s.add_parser("chat",help="Private engineering chat; always local-only"); ch.add_argument("text")
    r=s.add_parser("research",help="Public cloud research only; no local context egress"); r.add_argument("query")
    i=s.add_parser("ingress",help="Download public URL into local quarantine"); i.add_argument("url"); i.add_argument("--max-bytes",type=int,default=50_000_000)
    ia=s.add_parser("ingress-approve",help="Human promotion of a quarantined public ingress artifact"); ia.add_argument("path"); ia.add_argument("--allow-unscanned",action="store_true"); ia.add_argument("--acknowledge-content-risk",action="store_true")
    k=s.add_parser("knowledge"); ks=k.add_subparsers(dest="action",required=True); ks.add_parser("build"); ks.add_parser("stats"); kq=ks.add_parser("search"); kq.add_argument("query"); kq.add_argument("--limit",type=int,default=10)
    ma=s.add_parser("machine"); mas=ma.add_subparsers(dest="action",required=True); md=mas.add_parser("detect"); md.add_argument("--write",action="store_true")
    return p

def main():
    a=build_parser().parse_args()
    if a.command=="doctor": return cmd_doctor()
    if a.command=="company": return cmd_company(a)
    if a.command=="mode": return cmd_mode(a)
    if a.command=="chat": return cmd_chat(a)
    if a.command=="research": return cmd_research(a)
    if a.command=="ingress": return cmd_ingress(a)
    if a.command=="ingress-approve": return cmd_ingress_approve(a)
    if a.command=="knowledge": return cmd_knowledge(a)
    if a.command=="machine": return cmd_machine(a)
    return 1

if __name__=="__main__": raise SystemExit(main())
