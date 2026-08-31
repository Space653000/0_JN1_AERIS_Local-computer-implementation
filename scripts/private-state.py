#!/usr/bin/env python3
"""Encrypted AERIS private-state export/import using the external `age` CLI.

Why age: Python's standard library has no suitable modern authenticated file encryption.
AERIS therefore refuses to create a "secure" portable private backup unless a real
age implementation is installed. No weak home-grown crypto is used.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ITEMS = [
    ".env",
    ".aeris/knowledge",
    ".aeris/state",
    ".aeris/ingress",
    "data",
    "logs",
    "evidence",
    "memory",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_age() -> str:
    exe = shutil.which("age")
    if not exe:
        raise RuntimeError(
            "The `age` CLI is required for encrypted AERIS private-state portability. "
            "AERIS refuses to substitute weak custom encryption. Install age, then rerun."
        )
    return exe


def selected_items() -> list[Path]:
    return [ROOT / item for item in DEFAULT_ITEMS if (ROOT / item).exists()]


def safe_member(name: str) -> bool:
    p = Path(name)
    return not p.is_absolute() and ".." not in p.parts


def export_state(output: Path, recipient: str | None) -> None:
    age = require_age()
    output.parent.mkdir(parents=True, exist_ok=True)
    items = selected_items()
    if not items:
        raise RuntimeError("No private/local AERIS state exists to export yet.")

    with tempfile.TemporaryDirectory(prefix="aeris-private-") as td:
        tar_path = Path(td) / "private-state.tar"
        with tarfile.open(tar_path, "w") as tf:
            for item in items:
                tf.add(item, arcname=str(item.relative_to(ROOT)), recursive=True)
        cmd = [age, "-o", str(output)]
        if recipient:
            cmd += ["-r", recipient]
        else:
            cmd += ["-p"]
        cmd.append(str(tar_path))
        subprocess.run(cmd, check=True)

    manifest = {
        "schema_version": 1,
        "kind": "AERIS_ENCRYPTED_PRIVATE_STATE",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "ciphertext": output.name,
        "ciphertext_sha256": sha256(output),
        "encryption": "age",
        "mode": "recipient" if recipient else "passphrase",
        "included_paths": [str(p.relative_to(ROOT)) for p in items],
        "source_commit": _git_head(),
        "warning": "This encrypted state is private. Do not commit it to the public repository.",
    }
    output.with_suffix(output.suffix + ".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=5).strip()
    except Exception:
        return "UNKNOWN"


def import_state(source: Path, identity: str | None) -> None:
    age = require_age()
    manifest_path = source.with_suffix(source.suffix + ".manifest.json")
    if not manifest_path.exists():
        raise RuntimeError(f"Missing backup manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = sha256(source)
    if actual != manifest.get("ciphertext_sha256"):
        raise RuntimeError("Encrypted backup SHA-256 does not match its manifest.")

    with tempfile.TemporaryDirectory(prefix="aeris-restore-") as td:
        tar_path = Path(td) / "private-state.tar"
        cmd = [age, "-d", "-o", str(tar_path)]
        if identity:
            cmd += ["-i", identity]
        cmd.append(str(source))
        subprocess.run(cmd, check=True)
        with tarfile.open(tar_path, "r") as tf:
            bad = [m.name for m in tf.getmembers() if not safe_member(m.name)]
            if bad:
                raise RuntimeError(f"Unsafe archive members refused: {bad[:5]}")
            if sys.version_info >= (3, 12):
                tf.extractall(ROOT, filter="data")
            else:
                tf.extractall(ROOT)
    print("AERIS encrypted private state restored. Run company status, tests, doctor and local acceptance before use.")


def main() -> int:
    p = argparse.ArgumentParser(description="AERIS encrypted private state backup/restore")
    sub = p.add_subparsers(dest="command", required=True)
    e = sub.add_parser("export")
    e.add_argument("output", type=Path)
    e.add_argument("--recipient", help="age recipient; omit for interactive passphrase mode")
    i = sub.add_parser("import")
    i.add_argument("source", type=Path)
    i.add_argument("--identity", help="age identity file for recipient-encrypted backup")
    a = p.parse_args()
    try:
        if a.command == "export":
            export_state(a.output, a.recipient)
        else:
            import_state(a.source, a.identity)
    except Exception as exc:
        print(f"AERIS private-state operation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
