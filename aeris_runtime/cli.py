"""Command-line interface for AERIS portable company runtime."""
from __future__ import annotations
import argparse
import json
import platform
import sys
from .company import validate_company_manifest
from .config import ROOT, load_config, set_persisted_mode
from .providers import ProviderError
from .router import ModelRouter

def cmd_company(args: argparse.Namespace) -> int:
    status = validate_company_manifest()
    payload = {
        "company_id": status.company_id,
        "valid": status.valid,
        "virtual_roles": status.role_count,
        "runtime_modes": status.modes,
        "errors": status.errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status.valid else 4

def cmd_doctor() -> int:
    company = validate_company_manifest()
    config = load_config()
    router = ModelRouter(config)
    local_ok, local_detail = router.local.health()
    core_state = ROOT / ".aeris" / "state" / "core-target.json"
    core_cache = ROOT / ".aeris" / "core-reference"
    print("AERIS Portable Company Doctor")
    print(f"python: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")
    print(f"company_manifest: {'VALID' if company.valid else 'INVALID'}")
    print(f"virtual_roles: {company.role_count}")
    print(f"runtime_mode: {config.mode}")
    print(f"local_provider: {'READY' if local_ok else 'UNAVAILABLE'} — {local_detail}")
    print(f"local_model: {config.local_model}")
    print(f"cloud_configured: {'YES' if config.cloud_configured else 'NO'}")
    print(f"cloud_fallback_to_local: {config.cloud_fallback_to_local}")
    print(f"core_cache: {'PRESENT' if core_cache.exists() else 'NOT_CACHED'}")
    if core_state.exists():
        try:
            state = json.loads(core_state.read_text(encoding='utf-8'))
            print(f"core_target_sha: {state.get('sha', 'UNKNOWN')}")
        except Exception:
            print("core_target_sha: STATE_INVALID")
    else:
        print("core_target_sha: BOOTSTRAP_LOCK_ONLY")
    if not company.valid:
        print(f"result: BLOCKED — company manifest invalid: {company.errors}")
        return 4
    if config.mode in {"offline", "local"} and not local_ok:
        print("result: BLOCKED — local/offline mode requires a reachable local AI server/model")
        return 2
    print("result: READY_WITH_LIMITS" if not local_ok else "result: READY")
    return 0

def cmd_mode(args: argparse.Namespace) -> int:
    if args.action == "show":
        print(load_config().mode)
        return 0
    path = set_persisted_mode(args.value)
    print(f"AERIS mode set to {args.value} ({path})")
    return 0

def cmd_chat(args: argparse.Namespace) -> int:
    config = load_config()
    router = ModelRouter(config)
    decision = router.decision()
    print(f"[route] mode={decision.mode} selected={decision.selected} reason={decision.reason}", file=sys.stderr)
    try:
        result = router.chat(args.text)
    except ProviderError as exc:
        print(f"AERIS provider error: {exc}", file=sys.stderr)
        return 3
    print(f"[{result.provider}:{result.model}]", file=sys.stderr)
    print(result.text)
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aeris", description="AERIS portable local-first company runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check portable company/runtime readiness")
    company = sub.add_parser("company", help="Inspect portable company image")
    company_sub = company.add_subparsers(dest="action", required=True)
    company_sub.add_parser("status")
    mode = sub.add_parser("mode", help="Show or set AI routing mode")
    mode_sub = mode.add_subparsers(dest="action", required=True)
    mode_sub.add_parser("show")
    mode_set = mode_sub.add_parser("set")
    mode_set.add_argument("value", choices=["offline", "local", "cloud", "auto"])
    chat = sub.add_parser("chat", help="Send one prompt through the configured model router")
    chat.add_argument("text")
    return parser

def main() -> int:
    args = build_parser().parse_args()
    if args.command == "doctor": return cmd_doctor()
    if args.command == "company": return cmd_company(args)
    if args.command == "mode": return cmd_mode(args)
    if args.command == "chat": return cmd_chat(args)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
