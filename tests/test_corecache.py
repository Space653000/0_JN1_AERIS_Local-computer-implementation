import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from aeris_runtime.corecache import SNAPSHOT_MANIFEST, verify_core_cache, verify_snapshot_dir


class CoreSnapshotTests(unittest.TestCase):
    def _make_snapshot(self, root: Path):
        payload = root / "docs" / "baseline.md"
        payload.parent.mkdir(parents=True)
        payload.write_text("AERIS canonical core snapshot test", encoding="utf-8")
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        manifest = {
            "schema_version": 1,
            "kind": "AERIS_READ_ONLY_CORE_SNAPSHOT",
            "repository": "Space653000/0_JN1_AERIS",
            "branch": "main",
            "core_sha": "a" * 40,
            "file_count": 1,
            "files": {"docs/baseline.md": digest},
            "remote_write": "NOT_PRESENT_SNAPSHOT",
        }
        (root / SNAPSHOT_MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")

    def test_valid_snapshot_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._make_snapshot(root)
            result = verify_snapshot_dir(root)
            self.assertTrue(result["valid"], result)

    def test_unhashed_extra_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._make_snapshot(root)
            (root / "extra.txt").write_text("unexpected", encoding="utf-8")
            result = verify_snapshot_dir(root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("unhashed" in item for item in result["errors"]))

    def test_checksum_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._make_snapshot(root)
            (root / "docs" / "baseline.md").write_text("tampered", encoding="utf-8")
            result = verify_snapshot_dir(root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("checksum mismatch" in item for item in result["errors"]))


@unittest.skipUnless(shutil.which("git"), "git required")
class CoreGitCacheTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    def _make_guarded_cache(self, td: str) -> tuple[Path, Path, str]:
        base = Path(td) / "core-reference"
        state = Path(td) / "core-target.json"
        base.mkdir()
        self._git(base, "init")
        self._git(base, "config", "user.email", "test@example.invalid")
        self._git(base, "config", "user.name", "AERIS Test")
        (base / "README.md").write_text("canonical", encoding="utf-8")
        self._git(base, "add", "README.md")
        self._git(base, "commit", "-m", "baseline")
        sha = self._git(base, "rev-parse", "HEAD")
        self._git(base, "remote", "add", "origin", "https://github.com/Space653000/0_JN1_AERIS.git")
        self._git(base, "remote", "set-url", "--push", "origin", "DISABLED://AERIS-CORE-READ-ONLY")
        self._git(base, "update-ref", "refs/remotes/origin/main", sha)
        self._git(base, "checkout", "--detach", sha)
        hook = base / ".git" / "hooks" / "pre-push"
        hook.write_text('#!/bin/sh\necho "DENIED" >&2\nexit 1\n', encoding="utf-8")
        state.write_text(
            json.dumps({"repository": "Space653000/0_JN1_AERIS", "branch": "main", "sha": sha}),
            encoding="utf-8",
        )
        return base, state, sha

    def test_guarded_clean_git_cache_passes(self):
        with tempfile.TemporaryDirectory() as td:
            base, state, _ = self._make_guarded_cache(td)
            result = verify_core_cache(base, state)
            self.assertTrue(result["valid"], result)

    def test_modified_worktree_fails(self):
        with tempfile.TemporaryDirectory() as td:
            base, state, _ = self._make_guarded_cache(td)
            (base / "README.md").write_text("tampered", encoding="utf-8")
            result = verify_core_cache(base, state)
            self.assertFalse(result["valid"])
            self.assertTrue(any("working tree" in item for item in result["errors"]))

    def test_head_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            base, state, sha = self._make_guarded_cache(td)
            self._git(base, "checkout", "--detach", sha)
            (base / "other.txt").write_text("local mutation", encoding="utf-8")
            self._git(base, "add", "other.txt")
            self._git(base, "commit", "-m", "unauthorized local core commit")
            result = verify_core_cache(base, state)
            self.assertFalse(result["valid"])
            self.assertTrue(any("HEAD" in item for item in result["errors"]))

    def test_wrong_fetch_remote_fails(self):
        with tempfile.TemporaryDirectory() as td:
            base, state, _ = self._make_guarded_cache(td)
            self._git(base, "remote", "set-url", "origin", "https://example.invalid/not-core.git")
            result = verify_core_cache(base, state)
            self.assertFalse(result["valid"])
            self.assertTrue(any("fetch URL mismatch" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
