"""Cloud/local/offline model router for AERIS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .config import RuntimeConfig
from .providers import OllamaProvider, OpenAICompatibleProvider, ProviderError, ProviderResult


@dataclass
class RouteDecision:
    mode: str
    selected: str
    reason: str


class ModelRouter:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.local = OllamaProvider(
            config.local_base_url,
            config.local_model,
            config.local_timeout_sec,
        )
        self.cloud = OpenAICompatibleProvider(
            config.cloud_base_url,
            config.cloud_model,
            config.cloud_api_key,
            config.cloud_timeout_sec,
        )

    def decision(self) -> RouteDecision:
        mode = self.config.mode
        if mode == "offline":
            return RouteDecision(mode, "local", "offline mode hard-denies cloud AI")
        if mode == "local":
            return RouteDecision(mode, "local", "local mode selected explicitly")
        if mode == "cloud":
            if self.cloud.configured:
                return RouteDecision(mode, "cloud", "cloud mode selected explicitly")
            if self.config.cloud_fallback_to_local:
                return RouteDecision(mode, "local", "cloud not configured; local fallback enabled")
            return RouteDecision(mode, "cloud", "cloud selected but not configured")

        healthy, detail = self.local.health()
        if healthy:
            return RouteDecision("auto", "local", f"local-first auto routing: {detail}")
        if self.cloud.configured:
            return RouteDecision("auto", "cloud", "local unavailable; cloud configured")
        return RouteDecision("auto", "local", "local unavailable and cloud not configured")

    def chat(self, user_text: str, system_prompt: str | None = None) -> ProviderResult:
        system = system_prompt or self.config.system_prompt
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ]
        decision = self.decision()

        if decision.selected == "local":
            try:
                return self.local.chat(messages)
            except ProviderError:
                if self.config.mode == "auto" and self.cloud.configured:
                    return self.cloud.chat(messages)
                raise

        try:
            return self.cloud.chat(messages)
        except ProviderError:
            if self.config.cloud_fallback_to_local and self.config.mode != "offline":
                healthy, _ = self.local.health()
                if healthy:
                    return self.local.chat(messages)
            raise
