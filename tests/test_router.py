import unittest
from unittest.mock import patch

from aeris_runtime.config import RuntimeConfig
from aeris_runtime.router import ModelRouter


def cfg(mode="auto", cloud=True, fallback=True):
    return RuntimeConfig(
        mode=mode,
        local_base_url="http://127.0.0.1:11434",
        local_model="qwen2.5:3b",
        local_timeout_sec=1,
        cloud_base_url="https://example.invalid/v1",
        cloud_model="cloud-model" if cloud else "",
        cloud_api_key="secret" if cloud else "",
        cloud_timeout_sec=1,
        cloud_fallback_to_local=fallback,
        system_prompt="test",
    )


class RouterTests(unittest.TestCase):
    def test_offline_always_selects_local(self):
        router = ModelRouter(cfg(mode="offline"))
        decision = router.decision()
        self.assertEqual(decision.selected, "local")
        self.assertIn("hard-denies cloud", decision.reason)

    def test_local_selects_local(self):
        self.assertEqual(ModelRouter(cfg(mode="local")).decision().selected, "local")

    def test_cloud_selects_cloud_when_configured(self):
        self.assertEqual(ModelRouter(cfg(mode="cloud", cloud=True)).decision().selected, "cloud")

    def test_cloud_falls_back_to_local_when_unconfigured(self):
        self.assertEqual(ModelRouter(cfg(mode="cloud", cloud=False, fallback=True)).decision().selected, "local")

    def test_auto_prefers_local_when_healthy(self):
        router = ModelRouter(cfg(mode="auto"))
        with patch.object(router.local, "health", return_value=(True, "ok")):
            self.assertEqual(router.decision().selected, "local")

    def test_auto_uses_cloud_when_local_unavailable(self):
        router = ModelRouter(cfg(mode="auto", cloud=True))
        with patch.object(router.local, "health", return_value=(False, "down")):
            self.assertEqual(router.decision().selected, "cloud")


if __name__ == "__main__":
    unittest.main()
