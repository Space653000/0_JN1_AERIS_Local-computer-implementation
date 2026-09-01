"""Privacy-aware cloud/local/offline model router for AERIS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .config import RuntimeConfig
from .privacy import CloudRequestPolicy, assert_cloud_safe, assert_public_query_content_safe
from .providers import OllamaProvider, OpenAICompatibleProvider, ProviderError, ProviderResult


@dataclass
class RouteDecision:
    mode: str
    selected: str
    reason: str
    workload: str = "private_engineering"


class ModelRouter:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.local = OllamaProvider(
            config.local_base_url,
            config.local_model,
            config.local_timeout_sec,
            network_scope=config.local_network_scope,
        )
        self.cloud = OpenAICompatibleProvider(config.cloud_base_url, config.cloud_model, config.cloud_api_key, config.cloud_timeout_sec)

    def decision(self, workload: str = "private_engineering") -> RouteDecision:
        mode = self.config.mode
        if workload != "public_research":
            return RouteDecision(mode, "local", "private/local company context is hard-routed to an endpoint that must pass local/trusted-LAN policy", workload)
        if mode in {"offline", "local"}:
            return RouteDecision(mode, "local", f"{mode} mode keeps public research local", workload)
        if mode == "cloud":
            if self.cloud.configured:
                return RouteDecision(mode, "cloud", "cloud mode selected for public research only", workload)
            return RouteDecision(mode, "local", "cloud unavailable; public research uses local provider", workload)
        healthy, detail = self.local.health()
        if healthy:
            return RouteDecision("auto", "local", f"local-first public research: {detail}", workload)
        if self.cloud.configured:
            return RouteDecision("auto", "cloud", "local unavailable; cloud allowed for public research only", workload)
        return RouteDecision("auto", "local", "no cloud configured; local selected", workload)

    def _messages(self, user_text: str, system_prompt: str | None = None) -> List[Dict[str, str]]:
        system = system_prompt or self.config.system_prompt
        return [{"role": "system", "content": system}, {"role": "user", "content": user_text}]

    def chat(self, user_text: str, system_prompt: str | None = None) -> ProviderResult:
        """Private engineering channel. Provider endpoint policy is enforced before network I/O."""
        return self.local.chat(self._messages(user_text, system_prompt))

    def public_research(self, query: str) -> ProviderResult:
        """Public-context-only channel. Never attaches local files/memory/evidence."""
        assert_cloud_safe(CloudRequestPolicy(workload="public_research"))
        assert_public_query_content_safe(query)
        decision = self.decision("public_research")
        messages = self._messages(
            query,
            "You are the AERIS public research gateway. Use only the public query supplied here. You have no access to local AERIS memory, evidence, customer data or files.",
        )
        if decision.selected == "cloud":
            try:
                return self.cloud.chat(messages)
            except ProviderError:
                if not self.config.cloud_fallback_to_local:
                    raise
                healthy, _ = self.local.health()
                if healthy:
                    return self.local.chat(messages)
                raise
        return self.local.chat(messages)
