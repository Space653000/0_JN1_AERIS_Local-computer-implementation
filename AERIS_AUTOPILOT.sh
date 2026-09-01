#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set +e
bash "$ROOT/scripts/autopilot.sh" "$@"
code=$?
set -e
if [[ $code -eq 0 && -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://127.0.0.1:8765/ >/dev/null 2>&1 || true
fi
exit "$code"
