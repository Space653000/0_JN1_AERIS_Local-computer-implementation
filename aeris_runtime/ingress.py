"""One-way public information ingress: cloud/public web -> local storage only."""
from __future__ import annotations

import hashlib
import json
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


def download_public_url(url: str, max_bytes: int = 50_000_000) -> dict:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https public ingress URLs are supported")
    out = _new_dir("web")
    req = urllib.request.Request(url, headers={"User-Agent": "AERIS-Public-Ingress/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
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
    meta = {"url": url, "bytes": len(data), "sha256": digest, "content_type": content_type, "saved_to": str(target)}
    (out / "manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta
