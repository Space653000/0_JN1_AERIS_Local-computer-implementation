"""Verification and snapshot tooling for the canonical read-only AERIS Core cache."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from .config import ROOT

CORE = ROOT / ".aeris" / "core-reference"
CORE_STATE = ROOT / ".aeris" / "state" / "core-target.json"
SNAPSHOT_MANIFEST = "CORE_SNAPSHOT_MANIFEST.json"
CANONICAL_FETCH_URL = "https://github.com/Space653000/0_JN1_AERIS.git"
CANONICAL_REPOSITORY = "Space653000/0_JN1_AERIS"
CANONICAL_BRANCH = "main"


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

    _tree_files(CORE)
    shutil.copytree(CORE, destination, ignore=ignore, symlinks=False)
    files = _tree_files(destination)
    manifest = {
        "schema_version": 1,
        "kind": "AERIS_READ_ONLY_CORE_SNAPSHOT",
        "repository": CANONICAL_REPOSITORY,
        "branch": CANONICAL_BRANCH,
        "core_sha": sha,
        "file_count": len(files),
        "files": files,
        "remote_write": "NOT_PRESENT_SNAPSHOT",
        "assurance_boundary": "per-file integrity only; provenance authenticity requires a separately trusted/signed manifest or digest",
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
    if manifest.get("repository") != CANONICAL_REPOSITORY or manifest.get("branch") != CANONICAL_BRANCH:
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
    if manifest.get("file_count") != len(expected):
        errors.append("snapshot file_count does not match files manifest")
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
    return {
        "valid": not errors,
        "mode": "snapshot",
        "core_sha": sha.lower() if sha else None,
        "files": len(actual),
        "errors": errors,
        "assurance_boundary": "integrity check only unless the manifest/digest is independently trusted or signed",
    }


def _git(base: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(base), *args],
        text=True,
        capture_output=True,
        timeout=15,
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout.strip()


def _verify_git_cache(base: Path, state_path: Path) -> dict:
    config = base / ".git" / "config"
    hook = base / ".git" / "hooks" / "pre-push"
    errors: list[str] = []
    sha: str | None = None

    if not config.exists():
        errors.append(".git/config missing")
        return {"valid": False, "mode": "git_cache", "core_sha": None, "errors": errors}

    try:
        fetch_url = _git(base, "remote", "get-url", "origin")
        if fetch_url != CANONICAL_FETCH_URL:
            errors.append(f"canonical Core fetch URL mismatch: {fetch_url}")
        push_url = _git(base, "remote", "get-url", "--push", "origin")
        if not push_url.startswith("DISABLED://"):
            errors.append(f"canonical Core push URL is not disabled: {push_url}")
    except Exception as exc:
        errors.append(str(exc))

    if not hook.exists():
        errors.append("deny pre-push hook missing")
    else:
        text = hook.read_text(encoding="utf-8", errors="replace").lower()
        if "exit 1" not in text or "denied" not in text:
            errors.append("pre-push hook does not contain expected deny behavior")

    if not state_path.exists():
        errors.append("core-target.json missing")
    else:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8-sig"))
            if state.get("repository") != CANONICAL_REPOSITORY or state.get("branch") != CANONICAL_BRANCH:
                errors.append("core-target authority does not match canonical Core")
            sha = str(state.get("sha", "")).lower().strip()
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                errors.append("core-target SHA is invalid")
        except Exception as exc:
            errors.append(f"core-target.json is invalid: {exc}")

    try:
        head = _git(base, "rev-parse", "HEAD").lower()
        origin_main = _git(base, "rev-parse", "refs/remotes/origin/main").lower()
        dirty = _git(base, "status", "--porcelain", "--untracked-files=all")
        symbolic = _git(base, "symbolic-ref", "-q", "HEAD", check=False)
        if symbolic:
            errors.append(f"Core cache HEAD must be detached, found symbolic ref: {symbolic}")
        if sha and head != sha:
            errors.append(f"Core cache HEAD {head} does not match recorded Core SHA {sha}")
        if sha and origin_main != sha:
            errors.append(f"origin/main {origin_main} does not match recorded Core SHA {sha}")
        if dirty:
            errors.append("Core cache working tree is modified or contains untracked files")
    except Exception as exc:
        errors.append(str(exc))

    return {"valid": not errors, "mode": "git_cache", "core_sha": sha, "errors": errors}


def verify_core_cache(base: Path | None = None, state_path: Path | None = None) -> dict:
    base = (base or CORE).resolve()
    if not base.exists():
        return {"valid": False, "mode": "missing", "errors": ["Core cache missing"]}
    if (base / ".git").is_dir():
        return _verify_git_cache(base, state_path or CORE_STATE)
    return verify_snapshot_dir(base)
