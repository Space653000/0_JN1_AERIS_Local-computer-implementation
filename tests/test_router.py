import unittest
from unittest.mock import patch
from aeris_runtime.config import RuntimeConfig
from aeris_runtime.providers import ProviderError, ProviderResult
from aeris_runtime.router import ModelRouter


def cfg(mode="auto", cloud=True, fallback=True):
    return RuntimeConfig(
        mode=mode,
        local_base_url="http://127.0.0.1:11434",
        local_model="qwen3:4b-instruct",
        local_timeout_sec=1,
        cloud_base_url="https://example.invalid/v1",
        cloud_model="cloud-model" if cloud else "",
        cloud_api_key="secret" if cloud else "",
        cloud_timeout_sec=1,
        cloud_fallback_to_local=fallback,
        system_prompt="test",
        local_network_scope="loopback",
    )


class RouterTests(unittest.TestCase):
    def test_private_engineering_is_always_local(self):
        for mode in ["offline", "local", "cloud", "auto"]:
            self.assertEqual(ModelRouter(cfg(mode=mode)).decision("private_engineering").selected, "local")

    def test_cloud_mode_allows_cloud_for_public_research(self):
        self.assertEqual(ModelRouter(cfg(mode="cloud")).decision("public_research").selected, "cloud")

    def test_offline_public_research_stays_local(self):
        self.assertEqual(ModelRouter(cfg(mode="offline")).decision("public_research").selected, "local")

    def test_auto_public_research_prefers_local_when_healthy(self):
        router = ModelRouter(cfg(mode="auto"))
        with patch.object(router.local, "health", return_value=(True, "ok")):
            self.assertEqual(router.decision("public_research").selected, "local")

    def test_auto_public_research_can_use_cloud_when_local_down(self):
        router = ModelRouter(cfg(mode="auto"))
        with patch.object(router.local, "health", return_value=(False, "down")):
            self.assertEqual(router.decision("public_research").selected, "cloud")

    def test_private_chat_never_calls_cloud(self):
        router = ModelRouter(cfg(mode="cloud"))
        with patch.object(router.local, "chat", return_value=ProviderResult("local", "m", "ok")) as local_chat, patch.object(router.cloud, "chat") as cloud_chat:
            self.assertEqual(router.chat("private").text, "ok")
            local_chat.assert_called_once()
            cloud_chat.assert_not_called()

    def test_cloud_failure_falls_back_only_when_policy_allows(self):
        router = ModelRouter(cfg(mode="cloud", fallback=True))
        with patch.object(router.cloud, "chat", side_effect=ProviderError("down")), patch.object(router.local, "health", return_value=(True, "ok")), patch.object(router.local, "chat", return_value=ProviderResult("local", "m", "fallback")):
            self.assertEqual(router.public_research("public weather facts").text, "fallback")

        no_fallback = ModelRouter(cfg(mode="cloud", fallback=False))
        with patch.object(no_fallback.cloud, "chat", side_effect=ProviderError("down")), patch.object(no_fallback.local, "health", return_value=(True, "ok")):
            with self.assertRaises(ProviderError):
                no_fallback.public_research("public weather facts")


if __name__ == "__main__":
    unittest.main()
