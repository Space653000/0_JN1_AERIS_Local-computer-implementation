"""Portable machine capability detection with no third-party dependencies."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


def _ram_gb() -> float | None:
    try:
        if os.name == "nt":
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"], text=True, timeout=5).strip()
            return round(int(out) / (1024**3), 1)
        pages = os.sysconf("SC_PHYS_PAGES")
        size = os.sysconf("SC_PAGE_SIZE")
        return round(pages * size / (1024**3), 1)
    except Exception:
        return None


def _gpu() -> str:
    if shutil.which("nvidia-smi"):
        try:
            return subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], text=True, timeout=5).strip()
        except Exception:
            return "NVIDIA detected"
    if Path("/etc/nv_tegra_release").exists():
        return "NVIDIA Jetson / Tegra"
    return "not_detected"


def detect() -> dict:
    system = platform.system().lower()
    machine = platform.machine().lower()
    gpu = _gpu()
    if "tegra" in gpu.lower() or Path("/etc/nv_tegra_release").exists():
        profile = "jetson-orin-family"
    elif system == "windows" and "nvidia" in gpu.lower():
        profile = "windows-nvidia-workstation"
    elif system == "windows":
        profile = "windows-cpu"
    elif system == "linux" and "nvidia" in gpu.lower():
        profile = "linux-x86-nvidia"
    else:
        profile = "generic-local"
    tools = {name: bool(shutil.which(name)) for name in ["git", "python", "python3", "ollama", "nvidia-smi", "matlab"]}
    return {"os": system, "architecture": machine, "ram_gb": _ram_gb(), "gpu": gpu, "profile": profile, "tools": tools}


def write_report(path: Path) -> dict:
    payload = detect()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
