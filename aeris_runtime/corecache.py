"""Verification and snapshot tooling for the canonical read-only AERIS Core cache."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from .config import ROOT

CORE = ROOT / ".aeris" / "core-reference"
CORE_STATE = ROOT / ".aeris" / "state" / "core-target.json"
SNAPSHOT_MANIFEST = "CORE_SNAPSHOT_MANIFEST.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree_files(base: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(base.rglob("*")):
        if ".git" in path.parts or path.name == SNAPSHOT_MANIFEST:
            continue
        if path.is_symlink():
            raise RuntimeError(f"Core snapshot refuses symlink: {path}")
        if path.is_file():
            files[path.relative_to(base).as_posix()] = _sha256(path)
    return files


def _core_sha() -> str:
    if not CORE_STATE.exists():
        raise RuntimeError("core-target.json is missing; synchronize and review canonical Core before snapshotting")
    payload = json.loads(CORE_STATE.read_text(encoding="utf-8-sig"))
    sha = str(payload.get("sha", "")).strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        raise RuntimeError("core-target.json does not contain a valid 40-character Core SHA")
    return sha.lower()


def create_snapshot(destination: Path) -> dict:
    if not CORE.exists():
        raise RuntimeError("Canonical Core cache does not exist. Run sync-core first.")
    sha = _core_sha()
    destination = destination.resolve()
    if destination == CORE.resolve() or CORE.resolve() in destination.parents:
        raise RuntimeError("Snapshot destination must not be inside the active Core cache")
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    def ignore(directory: str, names: list[str]):
        ignored = []
        if Path(directory).resolve() == CORE.resolve() and ".git" in names:
            ignored.append(".git")
        if SNAPSHOT_MANIFEST in names:
            ignored.append(SNAPSHOT_MANIFEST)
        return ignored

    # Refuse links before copy so the snapshot cannot silently capture external content.
    _tree_files(CORE)
    shutil.copytree(CORE, destination, ignore=ignore, symlinks=False)
    files = _tree_files(destination)
    manifest = {
        "schema_version": 1,
        "kind": "AERIS_READ_ONLY_CORE_SNAPSHOT",
        "repository": "Space653000/0_JN1_AERIS",
        "branch": "main",
        "core_sha": sha,
        "file_count": len(files),
        "files": files,
        "remote_write": "NOT_PRESENT_SNAPSHOT",
    }
    (destination / SNAPSHOT_MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_snapshot_dir(base: Path) -> dict:
    manifest_path = base / SNAPSHOT_MANIFEST
    if not manifest_path.exists():
        return {"valid": False, "mode": "snapshot", "errors": ["CORE_SNAPSHOT_MANIFEST.json missing"]}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"valid": False, "mode": "snapshot", "errors": [f"invalid snapshot manifest: {exc}"]}
    errors: list[str] = []
    if manifest.get("kind") != "AERIS_READ_ONLY_CORE_SNAPSHOT":
        errors.append("unexpected snapshot kind")
    if manifest.get("repository") != "Space653000/0_JN1_AERIS" or manifest.get("branch") != "main":
        errors.append("snapshot authority does not match canonical Core")
    sha = str(manifest.get("core_sha", ""))
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        errors.append("snapshot Core SHA is invalid")
    expected = manifest.get("files")
    if not isinstance(expected, dict):
        errors.append("snapshot files manifest is invalid")
        expected = {}
    try:
        actual = _tree_files(base)
    except Exception as exc:
        errors.append(str(exc))
        actual = {}
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))[:10]
        extra = sorted(set(actual) - set(expected))[:10]
        if missing:
            errors.append(f"snapshot files missing: {missing}")
        if extra:
            errors.append(f"snapshot contains unhashed files: {extra}")
    for rel in sorted(set(actual) & set(expected)):
        if actual[rel].lower() != str(expected[rel]).lower():
            errors.append(f"checksum mismatch: {rel}")
            if len(errors) >= 20:
                break
    return {"valid": not errors, "mode": "snapshot", "core_sha": sha.lower() if sha else None, "files": len(actual), "errors": errors}


def _verify_git_cache(base: Path) -> dict:
    config = base / ".git" / "config"
    hook = base / ".git" / "hooks" / "pre-push"
    errors: list[str] = []
    if not config.exists():
        errors.append(".git/config missing")
    else:
        text = config.read_text(encoding="utf-8", errors="replace")
        compact = re.sub(r"\s+", "", text).lower()
        if "pushurl=disabled://aeris-core-read-only" not in compact:
            errors.append("canonical Core git cache push URL is not disabled")
    if not hook.exists():
        errors.append("deny pre-push hook missing")
    else:
        text = hook.read_text(encoding="utf-8", errors="replace").lower()
        if "exit 1" not in text or "denied" not in text:
            errors.append("pre-push hook does not contain expected deny behavior")
    sha = None
    if CORE_STATE.exists():
        try:
            sha = str(json.loads(CORE_STATE.read_text(encoding="utf-8-sig")).get("sha", "")).lower()
        except Exception:
            errors.append("core-target.json is invalid")
    else:
        errors.append("core-target.json missing")
    if sha and not re.fullmatch(r"[0-9a-f]{40}", sha):
        errors.append("core-target SHA is invalid")
    return {"valid": not errors, "mode": "git_cache", "core_sha": sha, "errors": errors}


def verify_core_cache(base: Path | None = None) -> dict:
    base = (base or CORE).resolve()
    if not base.exists():
        return {"valid": False, "mode": "missing", "errors": ["Core cache missing"]}
    if (base / ".git").is_dir():
        return _verify_git_cache(base)
    return verify_snapshot_dir(base)
