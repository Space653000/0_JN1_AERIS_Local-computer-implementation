#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo '== AERIS Local Bootstrap =='
command -v python3 >/dev/null 2>&1 || { echo 'Python 3.10+ is required.' >&2; exit 1; }

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
mkdir -p .aeris/state data logs
if [ ! -f .env ]; then
  cp .env.example .env
  echo 'Created .env from .env.example'
fi

if command -v git >/dev/null 2>&1; then
  if ! "$ROOT/scripts/sync-core.sh"; then
    echo 'WARNING: core sync failed or network unavailable; offline operation is allowed.' >&2
  fi
fi

PY="$ROOT/.venv/bin/python"
"$PY" -m unittest discover -s tests -v
if ! "$PY" -m aeris_runtime doctor; then
  echo 'WARNING: doctor is not READY until a local AI server/model is available.' >&2
fi

echo 'Bootstrap completed.'
echo './scripts/run.sh mode set local'
echo './scripts/run.sh chat "hello"'
