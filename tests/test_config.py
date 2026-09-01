import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime.config import _secret, load_dotenv


class ConfigTests(unittest.TestCase):
    def test_dotenv_accepts_utf8_bom(self):
        key = "AERIS_TEST_BOM_KEY_91371"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / ".env"
            path.write_text("\ufeff" + key + "=works\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop(key, None)
                load_dotenv(path)
                self.assertEqual(os.environ.get(key), "works")
                os.environ.pop(key, None)

    def test_secret_file_is_supported_without_direct_secret(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "secret.txt"
            path.write_text("secret-value\n", encoding="utf-8")
            with patch.dict(os.environ, {"AERIS_TEST_SECRET_FILE": str(path)}, clear=False):
                os.environ.pop("AERIS_TEST_SECRET", None)
                self.assertEqual(_secret("AERIS_TEST_SECRET", "AERIS_TEST_SECRET_FILE"), "secret-value")


if __name__ == "__main__":
    unittest.main()
