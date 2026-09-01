"""Replaceable AERIS AI provider adapters using Python standard library only."""

from __future__ import annotations

import ipaddress
import json
import urllib.error
import urllib.parse
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


_RFC1918 = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)
_ULA = ipaddress.ip_network("fc00::/7")


def _trusted_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.is_loopback:
        return True
    if isinstance(ip, ipaddress.IPv4Address):
        return any(ip in network for network in _RFC1918)
    return ip in _ULA


def assert_private_local_endpoint(base_url: str, network_scope: str = "loopback") -> None:
    """Fail closed if a private-engineering provider is not actually local/trusted-LAN.

    `loopback` permits only localhost or literal loopback addresses.
    `trusted_lan` is an explicit Human opt-in and permits only literal RFC1918/ULA/loopback
    addresses. Arbitrary hostnames are rejected so DNS rebinding cannot turn a trusted-LAN
    name into a public destination between validation and connection.
    """
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        raise ProviderError("Private local provider URL must use http or https")
    if parsed.username or parsed.password:
        raise ProviderError("Private local provider URL must not embed credentials")
    if parsed.query or parsed.fragment:
        raise ProviderError("Private local provider URL must not contain query or fragment components")
    host = parsed.hostname
    if not host:
        raise ProviderError("Private local provider URL must contain a host")
    if network_scope not in {"loopback", "trusted_lan"}:
        raise ProviderError(f"Invalid AERIS_LOCAL_NETWORK_SCOPE: {network_scope}")

    if host.lower() == "localhost":
        if network_scope != "loopback" and network_scope != "trusted_lan":
            raise ProviderError("localhost scope rejected")
        return

    try:
        ip = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ProviderError(
            "Private engineering provider hostnames are forbidden. Use localhost for loopback, "
            "or a literal RFC1918/ULA IP with AERIS_LOCAL_NETWORK_SCOPE=trusted_lan."
        ) from exc

    if network_scope == "loopback" and not ip.is_loopback:
        raise ProviderError(f"Private engineering provider must be loopback, got {ip}")
    if network_scope == "trusted_lan" and not _trusted_private_ip(ip):
        raise ProviderError(f"Trusted-LAN private provider must use RFC1918/ULA/loopback address, got {ip}")


class OllamaProvider:
    name = "local-ollama"

    def __init__(self, base_url: str, model: str, timeout: int = 120, network_scope: str = "loopback") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.network_scope = network_scope

    def _assert_endpoint(self) -> None:
        assert_private_local_endpoint(self.base_url, self.network_scope)

    def health(self) -> tuple[bool, str]:
        """Return READY only when endpoint policy, Ollama and configured model are available."""
        try:
            self._assert_endpoint()
            data = _request_json(f"{self.base_url}/api/tags", timeout=min(self.timeout, 5))
            models = [m.get("name", "") for m in data.get("models", [])]
            if self.model in models or any(m.startswith(self.model + ":") for m in models):
                return True, f"reachable; model {self.model} available; scope={self.network_scope}"
            return False, f"reachable, but configured model {self.model} is not installed"
        except ProviderError as exc:
            return False, str(exc)

    def chat(self, messages: List[Dict[str, str]]) -> ProviderResult:
        self._assert_endpoint()
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
            raise ProviderError(
                "Cloud provider is not configured. Supply model plus API key through process environment, "
                "AERIS_CLOUD_API_KEY_FILE, or a local gitignored .env."
            )
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
