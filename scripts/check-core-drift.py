#!/usr/bin/env python3
"""Fail when the implementation baseline differs from the frozen Blueprint tag.

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
    tag = str(lock.get("tag", "")).strip()
    if tag != "v0.7.0-blueprint.1" or expected != "64576bdbe680170fc1ea27306d1a2ab494cac733":
        print("CORE_DRIFT_GATE=FAIL: finalized Blueprint identity changed", file=sys.stderr)
        return 4
    try:
        out = subprocess.check_output(
            ["git", "ls-remote", repo, f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
            text=True,
            timeout=30,
            stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        print(f"CORE_DRIFT_GATE=ERROR: unable to read canonical Core: {exc}", file=sys.stderr)
        return 3
    refs = dict((line.split()[1], line.split()[0]) for line in out.splitlines() if len(line.split()) == 2)
    actual = refs.get(f"refs/tags/{tag}^{{}}", refs.get(f"refs/tags/{tag}", ""))
    if not actual:
        print("CORE_DRIFT_GATE=ERROR: canonical Core returned no branch SHA", file=sys.stderr)
        return 3
    print(f"core_expected={expected}")
    print(f"core_actual={actual}")
    if actual != expected:
        print(
            "CORE_DRIFT_GATE=FAIL: frozen Blueprint tag identity mismatch. BLOCKED; do not repin automatically.",
            file=sys.stderr,
        )
        return 4
    print("CORE_DRIFT_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
