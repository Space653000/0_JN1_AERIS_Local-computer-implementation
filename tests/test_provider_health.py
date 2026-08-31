import unittest
from unittest.mock import patch

from aeris_runtime.providers import OllamaProvider


class ProviderHealthTests(unittest.TestCase):
    def test_reachable_ollama_without_configured_model_is_not_ready(self):
        provider = OllamaProvider("http://127.0.0.1:11434", "qwen3:4b-instruct", 1)
        with patch("aeris_runtime.providers._request_json", return_value={"models": [{"name": "other:latest"}]}):
            ok, detail = provider.health()
        self.assertFalse(ok)
        self.assertIn("not installed", detail)

    def test_configured_model_is_ready(self):
        provider = OllamaProvider("http://127.0.0.1:11434", "qwen3:4b-instruct", 1)
        with patch("aeris_runtime.providers._request_json", return_value={"models": [{"name": "qwen3:4b-instruct"}]}):
            ok, _ = provider.health()
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
