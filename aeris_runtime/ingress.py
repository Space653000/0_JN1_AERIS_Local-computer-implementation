"""One-way public information ingress: public internet/cloud -> local storage only."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
import time
import urllib.parse
import urllib.request
from pathlib import Path

from .config import ROOT, load_config
from .privacy import CloudRequestPolicy, assert_cloud_safe
from .router import ModelRouter

INGRESS_ROOT = ROOT / ".aeris" / "ingress"


def _new_dir(kind: str) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = INGRESS_ROOT / kind / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def public_cloud_query(query: str) -> dict:
    assert_cloud_safe(CloudRequestPolicy(workload="public_research"))
    cfg = load_config()
    router = ModelRouter(cfg)
    result = router.public_research(query)
    out = _new_dir("cloud")
    payload = {
        "query": query,
        "provider": result.provider,
        "model": result.model,
        "response": result.text,
        "privacy": "public_query_only_no_local_context",
    }
    (out / "result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "response.md").write_text(result.text, encoding="utf-8")
    return {"saved_to": str(out), **payload}


def _assert_public_url(url: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https public ingress URLs are supported")
    if parsed.username or parsed.password:
        raise ValueError("Credentials embedded in ingress URLs are forbidden")
    host = parsed.hostname
    if not host:
        raise ValueError("Ingress URL must contain a hostname")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve ingress hostname: {host}") from exc
    if not addresses:
        raise ValueError("Ingress hostname resolved to no addresses")
    for raw in addresses:
        ip = ipaddress.ip_address(raw.split("%", 1)[0])
        if not ip.is_global:
            raise ValueError(f"Ingress denied for non-public address: {ip}")
    return parsed


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        _assert_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_public_url(url: str, max_bytes: int = 50_000_000) -> dict:
    cfg = load_config()
    if cfg.mode == "offline":
        raise RuntimeError("External URL ingress is disabled in AERIS offline mode")
    _assert_public_url(url)
    if max_bytes <= 0 or max_bytes > 250_000_000:
        raise ValueError("max_bytes must be between 1 and 250,000,000")
    out = _new_dir("web")
    req = urllib.request.Request(url, headers={"User-Agent": "AERIS-Public-Ingress/1.1"})
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    with opener.open(req, timeout=60) as resp:
        final_url = resp.geturl()
        _assert_public_url(final_url)
        data = resp.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"Download exceeds {max_bytes} byte safety limit")
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
    digest = hashlib.sha256(data).hexdigest()
    ext = ".bin"
    if "json" in content_type:
        ext = ".json"
    elif "html" in content_type:
        ext = ".html"
    elif "text" in content_type:
        ext = ".txt"
    target = out / f"payload{ext}"
    target.write_bytes(data)
    meta = {
        "requested_url": url,
        "final_url": final_url,
        "bytes": len(data),
        "sha256": digest,
        "content_type": content_type,
        "saved_to": str(target),
        "classification": "PUBLIC_INGRESS_LOCAL_COPY",
    }
    (out / "manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta
