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
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import aeris_runtime.operations as operations
from tests.browser_e2e import find_browser

VIEWPORT = (1440, 1000)
ARTIFACT_ROOT = ROOT / ".aeris" / "evidence" / "browser-visual" / "latest"
ROUTES = (
    "/?theme=dark&visual_baseline=1",
    "/workspace?theme=dark&visual_baseline=1",
    "/services?theme=dark&visual_baseline=1",
    "/?theme=light&visual_baseline=1",
    "/workspace?theme=light&visual_baseline=1",
    "/services?theme=light&visual_baseline=1",
)


def _dom_fingerprints(html: str) -> dict[str,str]:
    """Report only DOM element IDs and digests; never publish runtime text."""
    class Fingerprints(HTMLParser):
        def __init__(self):
            super().__init__();self.stack=[];self.parts={}
        def handle_starttag(self,tag,attrs):
            identifier=dict(attrs).get('id')
            if identifier:self.parts.setdefault(identifier,[])
            self.stack.append((tag,identifier))
            token=json.dumps([tag,sorted(attrs)],ensure_ascii=False)
            for _,key in self.stack:
                if key:self.parts[key].append(token)
            if tag in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
                self.stack.pop()
        def handle_endtag(self,tag):
            for i in range(len(self.stack)-1,-1,-1):
                if self.stack[i][0]==tag:
                    del self.stack[i:];break
        def handle_data(self,data):
            for _,key in self.stack:
                if key:self.parts[key].append(data)
    parser=Fingerprints();parser.feed(html)
    return {key:hashlib.sha256(''.join(parts).encode('utf-8')).hexdigest() for key,parts in parser.parts.items()}


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
        "--dump-dom",
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
    return {"bytes": size, "sha256": digest, "width": width, "height": height,
            "dom_sha256":hashlib.sha256(proc.stdout.encode('utf-8')).hexdigest(),
            "element_digests":_dom_fingerprints(proc.stdout)}


def _check_accessibility_contract() -> list[str]:
    html = "\n".join((ROOT / "ui" / "web" / name).read_text(encoding="utf-8") for name in ("dashboard.html", "workspace.html", "services.html"))
    js = (ROOT / "ui" / "web" / "aeris-live.js").read_text(encoding="utf-8")
    required = ['<html lang="zh-Hant">', "setAttribute('aria-label','AERIS 主要導覽')", "main.id='mainContent'", "setAttribute('role','status')", "setAttribute('aria-live','polite')", "label.htmlFor=id", "setAttribute('aria-label','搜尋角色')"]
    missing = [marker for marker in required if marker not in html and marker not in js]
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
        snapshots = {}
        class SnapshotHandler(operations._Handler):
            def do_GET(self):
                if self.path in snapshots:
                    self._json(200, snapshots[self.path])
                else:
                    super().do_GET()
        server = ThreadingHTTPServer(("127.0.0.1", 0), SnapshotHandler)
        server.shutdown_token = "ci-browser-visual-only"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            # Snapshot actual GET responses once: otherwise new workflow runs and
            # telemetry between captures make pixel equality an invalid assertion.
            for endpoint in ('status','services','machine','roles','workflows','audit?limit=12',
                             'maturity','standards?q=','projects','tasks','capabilities','capabilities/roles/R001'):
                path='/api/v1/'+endpoint
                with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}'+path, timeout=30) as response:
                    value=json.load(response)
                if endpoint=='services' and not value.get('assessment_complete',True):
                    from aeris_runtime.telemetry import wait_for_service_telemetry
                    if not wait_for_service_telemetry(15):
                        raise AssertionError('service assessment did not complete for visual baseline')
                    with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}'+path,timeout=3) as response:
                        value=json.load(response)
                    if not value.get('assessment_complete'):
                        raise AssertionError('visual baseline cannot freeze pending/stale service truth')
                snapshots[path]=value
            browser = find_browser()
            route_results: list[dict[str, object]] = []
            route_hashes: set[str] = set()
            ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
            test_temp = ROOT / ".aeris" / "test-temp"
            test_temp.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="aeris-browser-visual-", dir=test_temp) as temp:
                temp_path = Path(temp)
                for index, route in enumerate(ROUTES):
                    profile = temp_path / f"profile-{index}"
                    profile.mkdir(parents=True, exist_ok=True)
                    url = f"http://127.0.0.1:{server.server_port}{route}"
                    first = _capture(browser, str(profile), url, temp_path / f"route-{index}-a.png")
                    second = _capture(browser, str(profile), url, temp_path / f"route-{index}-b.png")
                    if first["sha256"] != second["sha256"]:
                        # Preserve the actual failures locally. Never replace the
                        # failed capture with a later passing image or relax equality.
                        for suffix in ('a','b'):
                            shutil.copy2(temp_path/f'route-{index}-{suffix}.png',ARTIFACT_ROOT/f'failure-route-{index}-{suffix}.png')
                        keys=set(first['element_digests'])|set(second['element_digests'])
                        print(json.dumps({'visual_mismatch_route':route,'first_sha256':first['sha256'],
                            'second_sha256':second['sha256'],'same_dom':first['dom_sha256']==second['dom_sha256'],
                            'changed_element_ids':sorted(k for k in keys if first['element_digests'].get(k)!=second['element_digests'].get(k))}),flush=True)
                        raise AssertionError(f"same-route render is not bit-exact repeatable in one CI environment: {route}")
                    route_hashes.add(str(first["sha256"]))
                    theme="light" if "theme=light" in route else "dark"
                    page="workspace" if "/workspace" in route else "services" if "/services" in route else "dashboard"
                    persisted=ARTIFACT_ROOT/f"{page}-{theme}.png"
                    shutil.copy2(temp_path / f"route-{index}-a.png", persisted)
                    route_results.append({"route": route, "repeatable_sha256": first["sha256"], "bytes": first["bytes"], "artifact": str(persisted)})
            if len(route_hashes) != len(ROUTES):
                raise AssertionError("dark/light dashboard/workspace/services screenshots are not visually distinct")
            report={
                "AERIS_BROWSER_VISUAL_ACCESSIBILITY_BASELINE": "PASS",
                "implementation_sha": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=5).strip(),
                "browser": browser,
                "viewport": {"width": VIEWPORT[0], "height": VIEWPORT[1]},
                "routes": route_results,
                "accessibility_markers_checked": len(accessibility),
                "api_snapshot_sha256": hashlib.sha256(json.dumps(snapshots, sort_keys=True).encode()).hexdigest(),
                "scope": "fixed-viewport screenshot creation + same-environment bit-exact repeatability using one frozen actual API snapshot + basic accessibility semantics; NOT cross-version pixel-golden regression or live-state acceptance",
            }
            (ARTIFACT_ROOT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    raise SystemExit(run())
