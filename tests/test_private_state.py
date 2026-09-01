import importlib.util
import tarfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "private-state.py"
spec = importlib.util.spec_from_file_location("aeris_private_state", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class PrivateStateTests(unittest.TestCase):
    def test_safe_relative_member(self):
        self.assertTrue(module.safe_member(".aeris/knowledge/aeris.sqlite3"))

    def test_parent_traversal_is_denied(self):
        self.assertFalse(module.safe_member("../secret.txt"))

    def test_absolute_path_is_denied(self):
        self.assertFalse(module.safe_member("/etc/passwd"))

    def test_windows_drive_path_is_denied(self):
        self.assertFalse(module.safe_member("C:\\Windows\\System32\\evil.txt"))

    def test_symlink_member_is_denied(self):
        member = tarfile.TarInfo("data/link")
        member.type = tarfile.SYMTYPE
        member.linkname = "../../secret"
        self.assertFalse(module.safe_member(member))

    def test_hardlink_member_is_denied(self):
        member = tarfile.TarInfo("data/hardlink")
        member.type = tarfile.LNKTYPE
        member.linkname = "data/other"
        self.assertFalse(module.safe_member(member))

    def test_fifo_member_is_denied(self):
        member = tarfile.TarInfo("data/fifo")
        member.type = tarfile.FIFOTYPE
        self.assertFalse(module.safe_member(member))


if __name__ == "__main__":
    unittest.main()
