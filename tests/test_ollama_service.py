import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import ollama_service


class OllamaServiceTests(unittest.TestCase):
    def test_direct_serve_scopes_every_writable_windows_path(self):
        temp_root = ollama_service.ROOT / ".aeris" / "test-temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root = Path(directory)
            executable = root / "ollama.exe"
            executable.touch()
            original_profile = os.environ.get("USERPROFILE")
            with patch.object(ollama_service, "ROOT", root), patch.object(ollama_service.subprocess, "Popen") as spawn:
                spawn.return_value.pid = 123
                self.assertEqual(ollama_service.start(str(executable), "http://127.0.0.1:11434"), 123)
                args, kwargs = spawn.call_args
                self.assertEqual(args[0], [str(executable), "serve"])
                for key in ("USERPROFILE", "LOCALAPPDATA", "APPDATA", "OLLAMA_MODELS", "TEMP", "TMP"):
                    self.assertTrue(Path(kwargs["env"][key]).is_relative_to(root))
                self.assertEqual(os.environ.get("USERPROFILE"), original_profile)

    def test_nonlocal_server_is_rejected_before_process_launch(self):
        with patch.object(ollama_service.subprocess, "Popen") as spawn:
            for url in ("https://example.com", "http://192.168.1.2:11434", "http://user:secret@localhost:11434"):
                with self.assertRaises(ValueError):
                    ollama_service.start("unused", url)
            spawn.assert_not_called()
