"""AERIS local runtime configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".aeris" / "state"
MODE_FILE = STATE_DIR / "mode.txt"


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader with no third-party dependency.

    `utf-8-sig` intentionally accepts the BOM written by Windows PowerShell 5.1.
    `.env` is local-only and gitignored; long-lived secrets should preferably be
    supplied through the process environment or AERIS_*_FILE references.
    """
    path = path or (ROOT / ".env")
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _secret(name: str, file_name: str) -> str:
    direct = os.getenv(name, "").strip()
    if direct:
        return direct
    path_raw = os.getenv(file_name, "").strip()
    if not path_raw:
        return ""
    path = Path(path_raw).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    try:
        return path.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return ""


@dataclass(frozen=True)
class RuntimeConfig:
    mode: str
    local_base_url: str
    local_model: str
    local_timeout_sec: int
    cloud_base_url: str
    cloud_model: str
    cloud_api_key: str
    cloud_timeout_sec: int
    cloud_fallback_to_local: bool
    system_prompt: str
    local_network_scope: str = "loopback"

    @property
    def cloud_configured(self) -> bool:
        return bool(self.cloud_base_url and self.cloud_model and self.cloud_api_key)


def get_persisted_mode() -> str | None:
    if not MODE_FILE.exists():
        return None
    value = MODE_FILE.read_text(encoding="utf-8-sig").strip().lower()
    return value if value in {"offline", "local", "cloud", "auto"} else None


def set_persisted_mode(mode: str) -> Path:
    mode = mode.lower().strip()
    if mode not in {"offline", "local", "cloud", "auto"}:
        raise ValueError(f"Unsupported mode: {mode}")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    MODE_FILE.write_text(mode + "\n", encoding="utf-8")
    return MODE_FILE


def load_config() -> RuntimeConfig:
    load_dotenv()
    persisted = get_persisted_mode()
    mode = persisted or os.getenv("AERIS_AI_MODE", "auto").lower().strip()
    if mode not in {"offline", "local", "cloud", "auto"}:
        mode = "auto"
    network_scope = os.getenv("AERIS_LOCAL_NETWORK_SCOPE", "loopback").lower().strip()
    if network_scope not in {"loopback", "trusted_lan"}:
        network_scope = "invalid"
    return RuntimeConfig(
        mode=mode,
        local_base_url=os.getenv("AERIS_LOCAL_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
        local_model=os.getenv("AERIS_LOCAL_MODEL", "qwen3:4b-instruct"),
        local_timeout_sec=_int("AERIS_LOCAL_TIMEOUT_SEC", 120),
        cloud_base_url=os.getenv("AERIS_CLOUD_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        cloud_model=os.getenv("AERIS_CLOUD_MODEL", ""),
        cloud_api_key=_secret("AERIS_CLOUD_API_KEY", "AERIS_CLOUD_API_KEY_FILE"),
        cloud_timeout_sec=_int("AERIS_CLOUD_TIMEOUT_SEC", 120),
        cloud_fallback_to_local=_bool("AERIS_CLOUD_FALLBACK_TO_LOCAL", True),
        system_prompt=os.getenv(
            "AERIS_SYSTEM_PROMPT",
            "You are AERIS, an evidence-first acoustic engineering runtime. Treat inference as inference, not measured fact.",
        ),
        local_network_scope=network_scope,
    )


def load_runtime_manifest() -> Dict[str, object]:
    path = ROOT / "config" / "runtime.json"
    return json.loads(path.read_text(encoding="utf-8-sig"))
