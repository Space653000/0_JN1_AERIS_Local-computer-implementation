#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-auto}"
MODEL="${AERIS_LOCAL_MODEL:-qwen2.5:3b}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo '=== AERIS One-Click Company Installer ==='
echo 'Privacy: local/private data never auto-egresses to public cloud.'

run_root(){ if [ "$(id -u)" -eq 0 ]; then "$@"; elif command -v sudo >/dev/null 2>&1; then sudo "$@"; else echo "Need administrator privilege for: $*" >&2; exit 2; fi; }
install_python(){
  if command -v apt-get >/dev/null 2>&1; then run_root apt-get update; run_root apt-get install -y python3 python3-venv python3-pip curl ca-certificates;
  elif command -v dnf >/dev/null 2>&1; then run_root dnf install -y python3 python3-pip curl ca-certificates;
  elif command -v yum >/dev/null 2>&1; then run_root yum install -y python3 python3-pip curl ca-certificates;
  elif command -v pacman >/dev/null 2>&1; then run_root pacman -Sy --noconfirm python python-pip curl ca-certificates;
  elif command -v zypper >/dev/null 2>&1; then run_root zypper --non-interactive install python3 python3-pip curl ca-certificates;
  else echo 'No supported package manager found. See docs/ONE_CLICK_INSTALL.md.' >&2; exit 2; fi
}

command -v python3 >/dev/null 2>&1 || install_python
if ! python3 -m venv .venv 2>/dev/null && [ ! -x .venv/bin/python ]; then
  install_python
  python3 -m venv .venv
fi
PY="$ROOT/.venv/bin/python"
[ -f .env ] || cp .env.example .env
mkdir -p .aeris/state .aeris/knowledge .aeris/ingress .aeris/installers data logs

if ! command -v ollama >/dev/null 2>&1; then
  STAGED="$ROOT/portable_assets/installers/ollama-install.sh"
  INSTALLER="$ROOT/.aeris/installers/ollama-install.sh"
  if [ -f "$STAGED" ]; then
    cp "$STAGED" "$INSTALLER"
    echo 'Using staged Ollama installer.'
  else
    echo 'Ollama not found; downloading official installer for one-click setup...'
    if command -v curl >/dev/null 2>&1; then curl -fsSL https://ollama.com/install.sh -o "$INSTALLER";
    elif command -v wget >/dev/null 2>&1; then wget -q https://ollama.com/install.sh -O "$INSTALLER";
    else install_python; curl -fsSL https://ollama.com/install.sh -o "$INSTALLER"; fi
  fi
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$INSTALLER" | tee "$INSTALLER.sha256"; fi
  chmod +x "$INSTALLER"
  bash "$INSTALLER"
fi

if command -v ollama >/dev/null 2>&1 && [ "${AERIS_SKIP_MODEL_PULL:-0}" != "1" ]; then
  ollama pull "$MODEL" || echo 'Model pull failed; use a staged offline model asset and rerun doctor.'
fi

"$PY" -m aeris_runtime mode set "$MODE"
"$PY" -m aeris_runtime machine detect --write
"$PY" -m aeris_runtime knowledge build
"$PY" -m unittest discover -s tests -v
"$PY" -m aeris_runtime company status
"$PY" -m aeris_runtime doctor || true
echo 'AERIS bootstrap finished.'
