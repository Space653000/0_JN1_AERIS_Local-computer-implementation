"""Real-browser screenshot repeatability + basic accessibility baseline for AERIS UI.

This gate proves that supported CI browsers can render deterministic screenshots at a
fixed viewport and that core navigation/form accessibility semantics are present.
It is NOT a cross-version pixel-golden visual regression suite and must not be
reported as one.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import aeris_runtime.operations as operations
from browser_e2e import find_browser

VIEWPORT = (1440, 1000)
ROUTES = ("/", "/workspace", "/services")


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"not a valid PNG screenshot: {path}")
    return struct.unpack(">II", data[16:24])


def _capture(browser: str, profile: str, url: str, output: Path) -> dict[str, object]:
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--metrics-recording-only",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=2500",
        f"--window-size={VIEWPORT[0]},{VIEWPORT[1]}",
        f"--user-data-dir={profile}",
        f"--screenshot={output}",
        url,
    ]
    if os.name != "nt":
        cmd.insert(2, "--no-sandbox")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40)
    if proc.returncode != 0:
        raise RuntimeError(f"browser screenshot failed: exit={proc.returncode}; stderr={proc.stderr[-1800:]}")
    if not output.is_file():
        raise AssertionError(f"browser did not create screenshot: {output}")
    size = output.stat().st_size
    if size < 5000:
        raise AssertionError(f"screenshot unexpectedly small/blank: {output} bytes={size}")
    width, height = _png_size(output)
    if (width, height) != VIEWPORT:
        raise AssertionError(f"unexpected screenshot dimensions {(width, height)} != {VIEWPORT}")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return {"bytes": size, "sha256": digest, "width": width, "height": height}


def _check_accessibility_contract() -> list[str]:
    html = (ROOT / "ui" / "web" / "index.html").read_text(encoding="utf-8")
    required = [
        '<html lang="zh-Hant">',
        'aria-label="AERIS 主要導覽"',
        'aria-label="儀表板"',
        'aria-label="工作區"',
        'aria-label="服務"',
        'role="status"',
        'aria-live="polite"',
        '<main id="mainContent">',
        '<label for="projectSelect">',
        '<label for="taskTitle">',
        '<label for="taskDescription">',
        '<label for="riskLevel">',
        '<label for="invokePrompt">',
        'aria-label="搜尋角色"',
        'aria-label="搜尋標準"',
        'aria-label="搜尋本機知識"',
    ]
    missing = [marker for marker in required if marker not in html]
    if missing:
        raise AssertionError(f"accessibility contract markers missing: {missing}")
    return required


def run() -> int:
    accessibility = _check_accessibility_contract()
    opening = {
        "operational_state": "OPEN_WITH_LIMITS",
        "company_complete": False,
        "runtime_mode": "auto",
        "limits": ["CI_BROWSER_VISUAL_FIXTURE_NOT_REAL_MACHINE_OPENING"],
    }
    with patch.object(operations, "assess_opening", return_value=opening), patch.object(operations, "_write_heartbeat", return_value=None), patch.object(operations, "_read_json", return_value=None):
        server = ThreadingHTTPServer(("127.0.0.1", 0), operations._Handler)
        server.shutdown_token = "ci-browser-visual-only"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            browser = find_browser()
            route_results: list[dict[str, object]] = []
            route_hashes: set[str] = set()
            with tempfile.TemporaryDirectory(prefix="aeris-browser-visual-") as temp:
                temp_path = Path(temp)
                for index, route in enumerate(ROUTES):
                    profile = temp_path / f"profile-{index}"
                    profile.mkdir(parents=True, exist_ok=True)
                    url = f"http://127.0.0.1:{server.server_port}{route}"
                    first = _capture(browser, str(profile), url, temp_path / f"route-{index}-a.png")
                    second = _capture(browser, str(profile), url, temp_path / f"route-{index}-b.png")
                    if first["sha256"] != second["sha256"]:
                        raise AssertionError(f"same-route render is not bit-exact repeatable in one CI environment: {route}")
                    route_hashes.add(str(first["sha256"]))
                    route_results.append({"route": route, "repeatable_sha256": first["sha256"], "bytes": first["bytes"]})
            if len(route_hashes) != len(ROUTES):
                raise AssertionError("dashboard/workspace/services screenshots are not visually distinct")
            print(json.dumps({
                "AERIS_BROWSER_VISUAL_ACCESSIBILITY_BASELINE": "PASS",
                "browser": browser,
                "viewport": {"width": VIEWPORT[0], "height": VIEWPORT[1]},
                "routes": route_results,
                "accessibility_markers_checked": len(accessibility),
                "scope": "fixed-viewport screenshot creation + same-environment bit-exact repeatability + basic accessibility semantics; NOT cross-version pixel-golden regression",
            }, ensure_ascii=False, indent=2))
            return 0
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    raise SystemExit(run())
