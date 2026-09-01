"""Portable machine capability detection with no third-party dependencies."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "config" / "machine_profiles"


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


def _profile(system: str, machine: str, gpu: str) -> str:
    x86 = machine in {"x86_64", "amd64", "x64"}
    jetson = "tegra" in gpu.lower() or Path("/etc/nv_tegra_release").exists()
    if jetson:
        return "jetson-orin-family"
    if system == "windows" and x86 and "nvidia" in gpu.lower():
        return "windows-nvidia-workstation"
    if system == "windows" and x86:
        return "windows-cpu"
    if system == "linux" and x86 and "nvidia" in gpu.lower():
        return "linux-x86-nvidia"
    if system == "linux" and x86:
        return "linux-x86-cpu"
    return "unsupported-unprofiled"


def detect() -> dict:
    system = platform.system().lower()
    machine = platform.machine().lower()
    gpu = _gpu()
    profile = _profile(system, machine, gpu)
    profile_path = PROFILE_ROOT / f"{profile}.json"
    supported = profile != "unsupported-unprofiled" and profile_path.exists()
    ram = _ram_gb()
    warnings: list[str] = []
    if ram is not None and ram < 8:
        warnings.append("less than 8 GB RAM; local model continuity may be impractical")
    if not supported:
        warnings.append("no versioned AERIS machine profile exists for this OS/architecture")
    tools = {name: bool(shutil.which(name)) for name in ["git", "python", "python3", "ollama", "nvidia-smi", "matlab"]}
    return {
        "os": system,
        "architecture": machine,
        "ram_gb": ram,
        "gpu": gpu,
        "profile": profile,
        "profile_file": str(profile_path.relative_to(ROOT)) if profile_path.exists() else None,
        "support_state": "SUPPORTED_BASELINE_NOT_VERIFIED" if supported else "UNSUPPORTED_PROFILE",
        "supported_baseline": supported,
        "warnings": warnings,
        "tools": tools,
        "truth": "profile support is not real-machine verification; local acceptance is still required",
    }


def write_report(path: Path) -> dict:
    payload = detect()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
