"""Start the Windows Ollama server directly with all writable state under AERIS."""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from .config import ROOT


def start(executable: str, base_url: str) -> int:
    url = urlsplit(base_url)
    if url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"} or url.username or url.password:
        raise ValueError("Ollama server must bind to an unauthenticated loopback endpoint")
    state = ROOT / ".aeris"
    profile = state / "ollama-profile"
    env = dict(os.environ)
    for name, path in {
        "USERPROFILE": profile, "LOCALAPPDATA": profile / "AppData" / "Local",
        "APPDATA": profile / "AppData" / "Roaming", "OLLAMA_MODELS": state / "models",
        "TEMP": state / "test-temp", "TMP": state / "test-temp",
    }.items():
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    env["OLLAMA_HOST"] = base_url
    logs = state / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "ollama-serve.log").open("ab") as out, (logs / "ollama-serve.err.log").open("ab") as err:
        process = subprocess.Popen(
            [str(Path(executable).resolve(strict=True)), "serve"], cwd=ROOT, env=env,
            stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    return process.pid


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    print(start(args.executable, args.base_url))
