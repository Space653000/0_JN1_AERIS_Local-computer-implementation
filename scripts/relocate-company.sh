#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-auto}"
case "$MODE" in auto|offline|local|cloud) ;; *) echo "mode must be auto/offline/local/cloud"; exit 2;; esac
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo 'AERIS Portable Company Relocation — POSIX'
bash "$ROOT/INSTALL_AERIS_LOCAL.sh"
PY="$ROOT/.venv/bin/python"; [ -x "$PY" ] || PY=python3
"$PY" -m aeris_runtime company status
"$PY" -m aeris_runtime mode set "$MODE"
if ! "$PY" -m aeris_runtime doctor; then
  echo 'WARNING: doctor not READY; install/restore local model and inference prerequisites, then rerun doctor.' >&2
fi
echo 'Relocation bootstrap complete.'
