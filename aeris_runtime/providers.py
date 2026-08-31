"""Replaceable AERIS AI provider adapters using Python standard library only."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderResult:
    provider: str
    model: str
    text: str


def _request_json(
    url: str,
    *,
    payload: Dict[str, Any] | None = None,
    headers: Dict[str, str] | None = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise ProviderError(f"Request failed for {url}: {exc}") from exc


class OllamaProvider:
    name = "local-ollama"

    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def health(self) -> tuple[bool, str]:
        try:
            data = _request_json(f"{self.base_url}/api/tags", timeout=min(self.timeout, 5))
            models = [m.get("name", "") for m in data.get("models", [])]
            if self.model in models or any(m.startswith(self.model + ":") for m in models):
                return True, f"reachable; model {self.model} available"
            return True, f"reachable; configured model {self.model} not found"
        except ProviderError as exc:
            return False, str(exc)

    def chat(self, messages: List[Dict[str, str]]) -> ProviderResult:
        data = _request_json(
            f"{self.base_url}/api/chat",
            payload={"model": self.model, "messages": messages, "stream": False},
            timeout=self.timeout,
        )
        try:
            text = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"Unexpected Ollama response: {data}") from exc
        return ProviderResult(provider=self.name, model=self.model, text=text)


class OpenAICompatibleProvider:
    name = "cloud-openai-compatible"

    def __init__(self, base_url: str, model: str, api_key: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model and self.api_key)

    def chat(self, messages: List[Dict[str, str]]) -> ProviderResult:
        if not self.configured:
            raise ProviderError("Cloud provider is not configured. Set model and API key in .env.")
        data = _request_json(
            f"{self.base_url}/chat/completions",
            payload={"model": self.model, "messages": messages, "stream": False},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Unexpected cloud provider response: {data}") from exc
        return ProviderResult(provider=self.name, model=self.model, text=text)
