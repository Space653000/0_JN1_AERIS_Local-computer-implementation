"""Real-browser semantic E2E for the dependency-free AERIS local UI.

This test deliberately verifies rendered browser behavior and SPA route activation.
It is not pixel-level visual regression and must never be reported as such.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import aeris_runtime.operations as operations


def find_browser() -> str:
    env = os.environ.get("AERIS_E2E_BROWSER", "").strip()
    candidates: list[str] = [env] if env else []
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    if os.name == "nt":
        roots = [
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("LOCALAPPDATA"),
        ]
        rels = [
            r"Google\Chrome\Application\chrome.exe",
            r"Microsoft\Edge\Application\msedge.exe",
        ]
        for root in roots:
            if root:
                candidates.extend(str(Path(root) / rel) for rel in rels)
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError("No supported Chrome/Chromium/Edge browser found for real-browser E2E")


def run() -> int:
    opening = {
        "operational_state": "OPEN_WITH_LIMITS",
        "company_complete": False,
        "runtime_mode": "auto",
        "limits": ["CI_BROWSER_E2E_FIXTURE_NOT_REAL_MACHINE_OPENING"],
    }
    with patch.object(operations, "assess_opening", return_value=opening), patch.object(operations, "_write_heartbeat", return_value=None), patch.object(operations, "_read_json", return_value=None):
        server = ThreadingHTTPServer(("127.0.0.1", 0), operations._Handler)
        server.shutdown_token = "ci-browser-e2e-only"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            browser = find_browser()
            routes = {
                "/": ('id="dashboard" class="view active-view"', "本機聲學工程公司"),
                "/workspace": ('id="workspace" class="view active-view"', "Dynamic Pod"),
                "/services": ('id="services" class="view active-view"', "Engineering Workflows"),
            }
            results = []
            with tempfile.TemporaryDirectory(prefix="aeris-browser-e2e-") as profile:
                for route, required in routes.items():
                    url = f"http://127.0.0.1:{server.server_port}{route}"
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
                        "--virtual-time-budget=2500",
                        f"--user-data-dir={profile}",
                        "--dump-dom",
                        url,
                    ]
                    if os.name != "nt":
                        cmd.insert(2, "--no-sandbox")
                    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=35)
                    if proc.returncode != 0:
                        raise RuntimeError(f"browser failed for {route}: exit={proc.returncode}; stderr={proc.stderr[-1500:]}")
                    dom = proc.stdout
                    missing = [marker for marker in required if marker not in dom]
                    if missing:
                        raise AssertionError(f"browser route {route} missing rendered markers: {missing}")
                    if "/assets/app.js" not in dom:
                        raise AssertionError(f"browser route {route} did not render the AERIS application shell")
                    results.append({"route": route, "http_render": "PASS", "active_view": required[0]})
            print(json.dumps({
                "AERIS_BROWSER_SEMANTIC_E2E": "PASS",
                "browser": browser,
                "routes": results,
                "scope": "real headless browser SPA route/render semantic E2E; NOT pixel visual regression",
            }, ensure_ascii=False, indent=2))
            return 0
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    raise SystemExit(run())
