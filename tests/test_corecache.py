import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aeris_runtime.corecache import SNAPSHOT_MANIFEST, verify_snapshot_dir


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


if __name__ == "__main__":
    unittest.main()
