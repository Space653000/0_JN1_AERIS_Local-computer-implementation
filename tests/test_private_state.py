import importlib.util
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


if __name__ == "__main__":
    unittest.main()
