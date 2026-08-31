#!/usr/bin/env python3
"""Fail when the implementation baseline no longer matches canonical Core main.

This script is intentionally read-only. It never writes to 0_JN1_AERIS.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "core.lock.json"


def main() -> int:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    expected = str(lock["baseline_sha"]).strip()
    repo = str(lock["core_repository"]).strip()
    branch = str(lock.get("branch", "main")).strip()
    try:
        out = subprocess.check_output(
            ["git", "ls-remote", repo, f"refs/heads/{branch}"],
            text=True,
            timeout=30,
            stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        print(f"CORE_DRIFT_GATE=ERROR: unable to read canonical Core: {exc}", file=sys.stderr)
        return 3
    actual = out.split()[0] if out else ""
    if not actual:
        print("CORE_DRIFT_GATE=ERROR: canonical Core returned no branch SHA", file=sys.stderr)
        return 3
    print(f"core_expected={expected}")
    print(f"core_actual={actual}")
    if actual != expected:
        print(
            "CORE_DRIFT_GATE=FAIL: canonical Core changed. Review the new Core read-only, update implementation, "
            "then deliberately refresh core.lock.json. Do not auto-accept drift.",
            file=sys.stderr,
        )
        return 4
    print("CORE_DRIFT_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
