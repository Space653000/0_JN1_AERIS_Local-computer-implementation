"""One-way public information ingress: public internet/cloud -> local quarantine.

Security properties of this baseline:
- only http/https URLs without embedded credentials;
- DNS results must be globally routable IP addresses;
- the actual TCP/TLS connection is pinned to a prevalidated IP to reduce DNS-rebinding TOCTOU;
- HTTPS still validates the original hostname through TLS SNI/certificate checks;
- every redirect is revalidated and repinned;
- downloaded content is quarantined, hashed, locally scanned when a supported scanner exists,
  and never auto-indexed into AERIS Knowledge.
"""
from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import os
import shutil
import socket
import ssl
import subprocess
import time
import urllib.parse
from pathlib import Path

from .config import ROOT, load_config
from .privacy import CloudRequestPolicy, assert_cloud_safe
from .router import ModelRouter

INGRESS_ROOT = ROOT / ".aeris" / "ingress"
REDIRECT_CODES = {301, 302, 303, 307, 308}
MAX_REDIRECTS = 5


def _new_dir(kind: str) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1_000_000_000:09d}"
    path = INGRESS_ROOT / kind / stamp
    path.mkdir(parents=True, exist_ok=False)
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
        "classification": "PUBLIC_RESEARCH_LOCAL_RECORD",
    }
    (out / "result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "response.md").write_text(result.text, encoding="utf-8")
    return {"saved_to": str(out), **payload}


def _resolve_public(host: str, port: int) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve ingress hostname: {host}") from exc
    addresses: list[str] = []
    for item in infos:
        raw = item[4][0].split("%", 1)[0]
        if raw not in addresses:
            addresses.append(raw)
    if not addresses:
        raise ValueError("Ingress hostname resolved to no addresses")
    for raw in addresses:
        ip = ipaddress.ip_address(raw)
        if not ip.is_global:
            raise ValueError(f"Ingress denied because hostname resolves to non-public address: {ip}")
    return addresses


def _assert_public_url(url: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https public ingress URLs are supported")
    if parsed.username or parsed.password:
        raise ValueError("Credentials embedded in ingress URLs are forbidden")
    if parsed.fragment:
        # Fragments are client-side only; strip them from fetch semantics to keep provenance deterministic.
        parsed = parsed._replace(fragment="")
    host = parsed.hostname
    if not host:
        raise ValueError("Ingress URL must contain a hostname")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    _resolve_public(host, port)
    return parsed


def _request_path(parsed: urllib.parse.ParseResult) -> str:
    path = parsed.path or "/"
    if parsed.params:
        path += ";" + parsed.params
    if parsed.query:
        path += "?" + parsed.query
    return path


def _host_header(parsed: urllib.parse.ParseResult) -> str:
    assert parsed.hostname
    default = 443 if parsed.scheme == "https" else 80
    port = parsed.port or default
    return parsed.hostname if port == default else f"{parsed.hostname}:{port}"


def _open_pinned(parsed: urllib.parse.ParseResult, ip: str, timeout: int):
    assert parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    raw = socket.create_connection((ip, port), timeout=timeout)
    if parsed.scheme == "https":
        context = ssl.create_default_context()
        wrapped = context.wrap_socket(raw, server_hostname=parsed.hostname)
        conn = http.client.HTTPSConnection(parsed.hostname, port, timeout=timeout, context=context)
        conn.sock = wrapped
    else:
        conn = http.client.HTTPConnection(parsed.hostname, port, timeout=timeout)
        conn.sock = raw
    return conn


def _fetch_once(url: str, max_bytes: int, timeout: int = 60) -> dict:
    parsed = _assert_public_url(url)
    assert parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = _resolve_public(parsed.hostname, port)
    errors: list[str] = []
    for ip in addresses:
        conn = None
        try:
            conn = _open_pinned(parsed, ip, timeout)
            conn.request(
                "GET",
                _request_path(parsed),
                headers={"Host": _host_header(parsed), "User-Agent": "AERIS-Public-Ingress/2.0", "Accept": "*/*"},
            )
            response = conn.getresponse()
            if response.status in REDIRECT_CODES:
                location = response.getheader("Location")
                if not location:
                    raise RuntimeError(f"Redirect {response.status} has no Location header")
                return {"redirect": urllib.parse.urljoin(url, location), "connected_ip": ip, "status": response.status}
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"HTTP status {response.status} {response.reason}")
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError(f"Download exceeds {max_bytes} byte safety limit")
            return {
                "data": data,
                "content_type": response.getheader("Content-Type", "application/octet-stream"),
                "connected_ip": ip,
                "status": response.status,
            }
        except (OSError, ssl.SSLError, http.client.HTTPException, RuntimeError) as exc:
            errors.append(f"{ip}: {exc}")
        finally:
            if conn is not None:
                conn.close()
    raise RuntimeError("All validated public IP connection attempts failed: " + " | ".join(errors[:5]))


def _content_risk_reasons(data: bytes, content_type: str) -> list[str]:
    reasons: list[str] = []
    if data.startswith(b"MZ"):
        reasons.append("Windows executable signature detected")
    elif data.startswith(b"\x7fELF"):
        reasons.append("ELF executable signature detected")
    elif data[:4] in {b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe"}:
        reasons.append("Mach-O executable signature detected")

    lower_ct = content_type.lower()
    if any(marker in lower_ct for marker in ("text", "json", "html", "xml", "javascript")):
        text = data[:2_000_000].decode("utf-8", errors="ignore").lower()
        markers = {
            "ignore previous instructions": "prompt-injection phrase: ignore previous instructions",
            "ignore all previous": "prompt-injection phrase: ignore all previous",
            "system prompt": "prompt-injection/system-prompt phrase",
            "developer message": "prompt-injection/developer-message phrase",
            "read local file": "instruction requests local-file access",
            "upload local": "instruction requests local upload",
            "exfiltrate": "possible exfiltration instruction",
        }
        for needle, label in markers.items():
            if needle in text:
                reasons.append(label)
    return reasons


def _local_malware_scan(path: Path) -> dict:
    clamscan = shutil.which("clamscan")
    if clamscan:
        proc = subprocess.run([clamscan, "--no-summary", str(path)], capture_output=True, text=True, timeout=180)
        return {"scanner": "clamscan", "status": "CLEAN" if proc.returncode == 0 else "THREAT_OR_ERROR", "exit_code": proc.returncode}

    if os.name == "nt":
        candidates: list[Path] = []
        program_data = os.getenv("ProgramData")
        program_files = os.getenv("ProgramFiles")
        if program_data:
            platform_root = Path(program_data) / "Microsoft" / "Windows Defender" / "Platform"
            if platform_root.exists():
                candidates.extend(sorted(platform_root.glob("*/MpCmdRun.exe"), reverse=True))
        if program_files:
            candidates.append(Path(program_files) / "Windows Defender" / "MpCmdRun.exe")
        for scanner in candidates:
            if scanner.exists():
                proc = subprocess.run(
                    [str(scanner), "-Scan", "-ScanType", "3", "-File", str(path), "-DisableRemediation"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return {"scanner": "Microsoft Defender", "status": "CLEAN" if proc.returncode == 0 else "THREAT_OR_ERROR", "exit_code": proc.returncode}
    return {"scanner": None, "status": "NOT_AVAILABLE"}


def download_public_url(url: str, max_bytes: int = 50_000_000) -> dict:
    cfg = load_config()
    if cfg.mode == "offline":
        raise RuntimeError("External URL ingress is disabled in AERIS offline mode")
    if max_bytes <= 0 or max_bytes > 250_000_000:
        raise ValueError("max_bytes must be between 1 and 250,000,000")

    current = url
    chain: list[str] = []
    result: dict | None = None
    for _ in range(MAX_REDIRECTS + 1):
        _assert_public_url(current)
        result = _fetch_once(current, max_bytes)
        if "redirect" not in result:
            break
        chain.append(current)
        current = str(result["redirect"])
    else:
        raise RuntimeError(f"Ingress exceeded {MAX_REDIRECTS} redirects")
    if result is None or "data" not in result:
        raise RuntimeError("Ingress did not produce a response body")

    data = result["data"]
    content_type = str(result["content_type"])
    digest = hashlib.sha256(data).hexdigest()
    out = _new_dir("quarantine")
    ext = ".bin"
    if "json" in content_type.lower():
        ext = ".json"
    elif "html" in content_type.lower():
        ext = ".html"
    elif "text" in content_type.lower():
        ext = ".txt"
    elif "pdf" in content_type.lower():
        ext = ".pdf"
    target = out / f"payload{ext}"
    target.write_bytes(data)
    risk_reasons = _content_risk_reasons(data, content_type)
    malware_scan = _local_malware_scan(target)
    meta = {
        "requested_url": url,
        "final_url": current,
        "redirect_chain": chain,
        "connected_ip": result.get("connected_ip"),
        "http_status": result.get("status"),
        "bytes": len(data),
        "sha256": digest,
        "content_type": content_type,
        "saved_to": str(target),
        "classification": "PUBLIC_INGRESS_QUARANTINED",
        "knowledge_auto_index": False,
        "approval_required": True,
        "content_risk_reasons": risk_reasons,
        "malware_scan": malware_scan,
    }
    (out / "manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def approve_quarantined_ingress(path: str, *, allow_unscanned: bool = False, acknowledge_content_risk: bool = False) -> dict:
    source = Path(path).expanduser().resolve()
    manifest_path = source if source.name == "manifest.json" else source / "manifest.json"
    if not manifest_path.exists():
        raise ValueError("Ingress approval requires a quarantine manifest.json")
    meta = json.loads(manifest_path.read_text(encoding="utf-8"))
    if meta.get("classification") != "PUBLIC_INGRESS_QUARANTINED":
        raise ValueError("Only PUBLIC_INGRESS_QUARANTINED artifacts can be approved")
    payload = Path(str(meta.get("saved_to", ""))).resolve()
    if not payload.exists() or hashlib.sha256(payload.read_bytes()).hexdigest() != meta.get("sha256"):
        raise ValueError("Quarantine payload is missing or checksum verification failed")
    scan = meta.get("malware_scan", {})
    if scan.get("status") == "THREAT_OR_ERROR":
        raise ValueError("Ingress approval refused because malware scan did not pass")
    if scan.get("status") != "CLEAN" and not allow_unscanned:
        raise ValueError("No clean malware scan exists; explicitly use --allow-unscanned only after Human review")
    if meta.get("content_risk_reasons") and not acknowledge_content_risk:
        raise ValueError("Content-risk markers exist; Human acknowledgement is required")

    out = _new_dir("approved")
    approved_payload = out / payload.name
    shutil.copy2(payload, approved_payload)
    approved = dict(meta)
    approved.update(
        {
            "classification": "PUBLIC_INGRESS_HUMAN_APPROVED",
            "saved_to": str(approved_payload),
            "approved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "knowledge_auto_index": False,
            "approval_basis": {
                "allow_unscanned": allow_unscanned,
                "acknowledge_content_risk": acknowledge_content_risk,
            },
        }
    )
    (out / "manifest.json").write_text(json.dumps(approved, ensure_ascii=False, indent=2), encoding="utf-8")
    return approved
