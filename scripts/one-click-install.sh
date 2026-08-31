#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-auto}"
MODEL="${AERIS_LOCAL_MODEL:-qwen2.5:3b}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo '=== AERIS One-Click Company Installer ==='
echo 'Policy: local data stays local; cloud is public-information ingress only.'
if ! command -v python3 >/dev/null 2>&1; then echo 'Python 3.10+ is required. Install it with your OS package manager, then rerun.' >&2; exit 2; fi
[ -d .venv ] || python3 -m venv .venv
PY="$ROOT/.venv/bin/python"
[ -f .env ] || cp .env.example .env
mkdir -p .aeris/state .aeris/knowledge .aeris/ingress data logs
if ! command -v ollama >/dev/null 2>&1; then
  echo 'Ollama not detected. See docs/deployment/LOCAL_AI_AND_MODELS.md or stage an offline asset pack.'
else
  if [ "${AERIS_SKIP_MODEL_PULL:-0}" != "1" ]; then ollama pull "$MODEL" || echo 'Model pull failed; continue with staged/offline model if available.'; fi
fi
"$PY" -m aeris_runtime mode set "$MODE"
"$PY" -m aeris_runtime machine detect --write
"$PY" -m aeris_runtime knowledge build
"$PY" -m unittest discover -s tests -v
"$PY" -m aeris_runtime company status
"$PY" -m aeris_runtime doctor || true
echo 'AERIS installation bootstrap finished.'
