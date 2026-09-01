#!/usr/bin/env python3
"""Encrypted AERIS private-state export/import using the external `age` CLI.

AERIS refuses weak custom encryption and rejects archive constructs that could escape
or alias the AERIS root during cross-platform restore.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
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
DEFAULT_MAX_RESTORE_BYTES = 500 * 1024**3


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


def _assert_no_source_links(items: list[Path]) -> None:
    for item in items:
        if item.is_symlink():
            raise RuntimeError(f"Private-state export refuses symlink source: {item}")
        if item.is_dir():
            for child in item.rglob("*"):
                if child.is_symlink():
                    raise RuntimeError(f"Private-state export refuses symlink inside source tree: {child}")


def safe_member(member: str | tarfile.TarInfo) -> bool:
    """Validate tar members independently of host OS path semantics and link behavior."""
    info = member if isinstance(member, tarfile.TarInfo) else None
    name = info.name if info is not None else member
    if not name or "\x00" in name:
        return False
    normalized = name.replace("\\", "/")
    posix = PurePosixPath(normalized)
    win = PureWindowsPath(name)
    if posix.is_absolute() or win.is_absolute() or win.drive:
        return False
    if normalized.startswith("//") or ".." in posix.parts or ".." in win.parts:
        return False
    if info is not None:
        # Links and special devices can escape or alias ROOT even with a safe-looking path.
        if info.issym() or info.islnk() or info.isdev() or info.isfifo():
            return False
        if not (info.isfile() or info.isdir()):
            return False
    return True


def export_state(output: Path, recipient: str | None) -> None:
    age = require_age()
    output.parent.mkdir(parents=True, exist_ok=True)
    items = selected_items()
    if not items:
        raise RuntimeError("No private/local AERIS state exists to export yet.")
    _assert_no_source_links(items)

    with tempfile.TemporaryDirectory(prefix="aeris-private-") as td:
        tar_path = Path(td) / "private-state.tar"
        with tarfile.open(tar_path, "w", dereference=False) as tf:
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
        "schema_version": 2,
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


def _max_restore_bytes() -> int:
    raw = os.getenv("AERIS_MAX_PRIVATE_RESTORE_BYTES", str(DEFAULT_MAX_RESTORE_BYTES))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError("AERIS_MAX_PRIVATE_RESTORE_BYTES must be an integer") from exc
    if value <= 0:
        raise RuntimeError("AERIS_MAX_PRIVATE_RESTORE_BYTES must be positive")
    return value


def import_state(source: Path, identity: str | None) -> None:
    age = require_age()
    manifest_path = source.with_suffix(source.suffix + ".manifest.json")
    if not manifest_path.exists():
        raise RuntimeError(f"Missing backup manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("kind") != "AERIS_ENCRYPTED_PRIVATE_STATE" or manifest.get("encryption") != "age":
        raise RuntimeError("Backup manifest is not an AERIS age-encrypted private-state artifact")
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
            members = tf.getmembers()
            bad = [m.name for m in members if not safe_member(m)]
            if bad:
                raise RuntimeError(f"Unsafe archive members refused: {bad[:5]}")
            total_size = sum(m.size for m in members if m.isfile())
            if total_size > _max_restore_bytes():
                raise RuntimeError(f"Private-state restore exceeds configured size limit: {total_size} bytes")
            if sys.version_info >= (3, 12):
                tf.extractall(ROOT, members=members, filter="data")
            else:
                # Safe because traversal, links and special members were all rejected above.
                tf.extractall(ROOT, members=members)
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
