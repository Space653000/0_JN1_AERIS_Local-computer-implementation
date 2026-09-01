"""Real-browser semantic E2E for the dependency-free AERIS local UI.

This test deliberately verifies rendered browser behavior and SPA route activation.
It is not pixel-level visual regression and must never be reported as such.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
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

BROWSER_TIMEOUT_SEC = 35
BROWSER_TIMEOUT_ATTEMPTS = 2


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


def _terminate_process_tree(proc: subprocess.Popen[str]) -> None:
    """Best-effort hard cleanup after a browser timeout; never converts failure to PASS."""
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    try:
        proc.communicate(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _run_browser_process(cmd: list[str], timeout: int = BROWSER_TIMEOUT_SEC) -> tuple[int, str, str]:
    kwargs: dict[str, object] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **kwargs)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(proc)
        raise
    return proc.returncode, stdout, stderr


def _dump_dom_with_bounded_timeout_retry(browser: str, url: str, route: str) -> str:
    timeouts: list[str] = []
    for attempt in range(1, BROWSER_TIMEOUT_ATTEMPTS + 1):
        # A new profile for every attempt prevents a timed-out Chrome process/profile lock
        # from contaminating the retry.
        with tempfile.TemporaryDirectory(prefix=f"aeris-browser-e2e-{attempt}-") as profile:
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
            try:
                returncode, stdout, stderr = _run_browser_process(cmd)
            except subprocess.TimeoutExpired:
                timeouts.append(f"attempt={attempt} timeout={BROWSER_TIMEOUT_SEC}s")
                continue
            if returncode != 0:
                raise RuntimeError(f"browser failed for {route}: exit={returncode}; stderr={stderr[-1500:]}")
            return stdout
    raise RuntimeError(
        f"browser timed out for {route} after {BROWSER_TIMEOUT_ATTEMPTS} isolated attempts: "
        + "; ".join(timeouts)
    )


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
                "/?theme=dark": ('id="dashboard" class="view active-view"', 'data-theme="dark"', "本機聲學工程公司"),
                "/workspace?theme=dark": ('id="workspace" class="view active-view"', 'data-theme="dark"', "Dynamic Pod"),
                "/services?theme=dark": ('id="services" class="view active-view"', 'data-theme="dark"', "Engineering Workflows"),
                "/?theme=light": ('id="dashboard" class="view active-view"', 'data-theme="light"', "本機聲學工程公司"),
                "/workspace?theme=light": ('id="workspace" class="view active-view"', 'data-theme="light"', "Dynamic Pod"),
                "/services?theme=light": ('id="services" class="view active-view"', 'data-theme="light"', "Engineering Workflows"),
            }
            results = []
            for route, required in routes.items():
                url = f"http://127.0.0.1:{server.server_port}{route}"
                dom = _dump_dom_with_bounded_timeout_retry(browser, url, route)
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
                "timeout_recovery": f"bounded {BROWSER_TIMEOUT_ATTEMPTS}-attempt isolated-profile retry; repeated timeout fails closed",
                "scope": "real headless browser SPA route/render semantic E2E; NOT pixel visual regression",
            }, ensure_ascii=False, indent=2))
            return 0
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    raise SystemExit(run())
