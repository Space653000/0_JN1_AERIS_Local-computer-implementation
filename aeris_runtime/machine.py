"""Portable machine capability detection with no third-party dependencies."""
from __future__ import annotations

import json
import ctypes
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .machine_qualification import qualify_facts

ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "config" / "machine_profiles"


def _ram_gb() -> float | None:
    try:
        if os.name == "nt":
            class MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatusEx()
            status.dwLength = ctypes.sizeof(status)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                raise OSError("GlobalMemoryStatusEx failed")
            return round(status.ullTotalPhys / (1024**3), 1)
        pages = os.sysconf("SC_PHYS_PAGES")
        size = os.sysconf("SC_PAGE_SIZE")
        return round(pages * size / (1024**3), 1)
    except Exception:
        return None


def _disk_free_gb() -> float | None:
    try:
        return round(shutil.disk_usage(ROOT).free / (1024**3), 1)
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


def _parse_vram_gb(lines: list[str]) -> float | None:
    """Return the largest numeric NVIDIA memory row, ignoring NPU/N/A rows."""
    values: list[float] = []
    for item in lines:
        value = item.strip()
        if not value:
            continue
        try:
            values.append(float(value) / 1024)
        except ValueError:
            continue
    return round(max(values), 2) if values else None


def _vram_gb() -> float | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            text=True,
            timeout=5,
        ).strip().splitlines()
        return _parse_vram_gb(out)
    except Exception:
        return None


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
    disk_free = _disk_free_gb()
    warnings: list[str] = []
    if ram is not None and ram < 8:
        warnings.append("less than 8 GB RAM; local model continuity may be impractical")
    if not supported:
        warnings.append("no versioned AERIS machine profile exists for this OS/architecture")
    tools = {name: bool(shutil.which(name)) for name in ["git", "python", "python3", "ollama", "nvidia-smi", "matlab"]}
    facts = {
        "os": system,
        "architecture": machine,
        "ram_gb": ram,
        "disk_free_gb": disk_free,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "gpu": gpu,
        "vram_gb": _vram_gb(),
        "profile": profile,
        "tools": tools,
    }
    qualification = qualify_facts(facts)
    support_state = "UNSUPPORTED_PROFILE"
    if supported:
        support_state = "SUPPORTED_PROFILE_QUALIFIED_BASELINE" if qualification["overall_state"] == "QUALIFIED_BASELINE" else "SUPPORTED_PROFILE_NOT_YET_QUALIFIED"
    return {
        **facts,
        "profile_file": str(profile_path.relative_to(ROOT)) if profile_path.exists() else None,
        "support_state": support_state,
        "supported_baseline": supported,
        "qualification": qualification,
        "warnings": warnings,
        "truth": "profile support and QUALIFIED_BASELINE are deterministic inventory checks, not real-machine verification; local acceptance, sustained-load/thermal/latency and external-tool evidence remain separate",
    }


def write_report(path: Path) -> dict:
    payload = detect()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
