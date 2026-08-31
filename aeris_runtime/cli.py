"""Command-line interface for AERIS local runtime."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from .config import ROOT, get_persisted_mode, load_config, set_persisted_mode
from .providers import ProviderError
from .router import ModelRouter


def cmd_doctor() -> int:
    config = load_config()
    router = ModelRouter(config)
    local_ok, local_detail = router.local.health()
    core_state = ROOT / ".aeris" / "state" / "core-target.json"
    core_cache = ROOT / ".aeris" / "core-reference"

    print("AERIS Local Runtime Doctor")
    print(f"python: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")
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

    if config.mode in {"offline", "local"} and not local_ok:
        print("result: BLOCKED — local/offline mode requires a reachable local AI server/model")
        return 2
    print("result: READY_WITH_LIMITS" if not local_ok else "result: READY")
    return 0


def cmd_mode(args: argparse.Namespace) -> int:
    if args.action == "show":
        config = load_config()
        print(config.mode)
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
    parser = argparse.ArgumentParser(prog="aeris", description="AERIS local-first AI runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check local runtime readiness")

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
    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "mode":
        return cmd_mode(args)
    if args.command == "chat":
        return cmd_chat(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
