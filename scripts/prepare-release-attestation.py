#!/usr/bin/env python3
"""Assemble a formal release-attestation task: computes the honest version
tuple, seals an Evidence bundle, and signs AERIS's own implementer
attestation. Prints the exact next command for the Human Chief Engineer to
run to add their own G5 approval -- this script never signs that part.

Usage:
    python scripts/prepare-release-attestation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aeris_runtime.release_attestation import prepare_release_task  # noqa: E402


def main() -> int:
    try:
        prepared = prepare_release_task()
    except ValueError as exc:
        print(f"Cannot prepare a release attestation right now: {exc}", file=sys.stderr)
        return 1

    print("Release attestation prepared:")
    print(f"  task_id: {prepared['task_id']}")
    print(f"  run_id:  {prepared['run_id']}")
    print(f"  version_tuple_sha256: {prepared['version_tuple_sha256']}")
    print()
    print("AERIS has signed its own implementer attestation for this exact")
    print("version. To formally approve this release, the Human Chief")
    print("Engineer now runs (using their OWN key from authority-keygen.py):")
    print()
    print(f"  python scripts/mint-g5-approval.py --key-file <your-key-file> "
          f"--signer-id <your-signer-id> --task-id {prepared['task_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
