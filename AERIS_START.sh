#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$ROOT/.venv/bin/python"
[[ -x "$PY" ]] || PY="$(command -v python3 || command -v python || true)"
[[ -n "$PY" ]] || { echo 'Python runtime not found. Run AERIS_AUTOPILOT.sh first.' >&2; exit 2; }
cd "$ROOT"
"$PY" -m aeris_runtime company open --actor AERIS_START --start-supervisor --port 8765
if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && command -v xdg-open >/dev/null 2>&1; then xdg-open http://127.0.0.1:8765/ >/dev/null 2>&1 || true; fi
