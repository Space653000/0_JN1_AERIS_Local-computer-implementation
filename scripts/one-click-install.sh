#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-auto}"
MODEL="${AERIS_LOCAL_MODEL:-qwen3:4b-instruct}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo '=== AERIS One-Click Company Installer ==='
echo 'Privacy: local/private data never auto-egresses to public cloud.'

run_root(){ if [ "$(id -u)" -eq 0 ]; then "$@"; elif command -v sudo >/dev/null 2>&1; then sudo "$@"; else echo "Need administrator privilege for: $*" >&2; exit 2; fi; }
install_python(){
  if command -v apt-get >/dev/null 2>&1; then run_root apt-get update; run_root apt-get install -y python3 python3-venv python3-pip curl ca-certificates git;
  elif command -v dnf >/dev/null 2>&1; then run_root dnf install -y python3 python3-pip curl ca-certificates git;
  elif command -v yum >/dev/null 2>&1; then run_root yum install -y python3 python3-pip curl ca-certificates git;
  elif command -v pacman >/dev/null 2>&1; then run_root pacman -Sy --noconfirm python python-pip curl ca-certificates git;
  elif command -v zypper >/dev/null 2>&1; then run_root zypper --non-interactive install python3 python3-pip curl ca-certificates git;
  else echo 'No supported package manager found. See docs/ONE_CLICK_INSTALL.md.' >&2; exit 2; fi
}
verify_python(){ python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 9)' || { echo 'AERIS requires Python 3.10 or newer.' >&2; exit 2; }; }
verify_staged_hash(){
  local file="$1" sidecar="$1.sha256"
  [ -f "$sidecar" ] || { echo "Staged installer requires SHA-256 sidecar: $sidecar" >&2; exit 3; }
  local expected actual
  expected="$(awk '{print tolower($1)}' "$sidecar" | head -1)"
  actual="$(sha256sum "$file" | awk '{print tolower($1)}')"
  [ "$expected" = "$actual" ] || { echo "SHA-256 mismatch for staged installer: $file" >&2; exit 3; }
}

command -v python3 >/dev/null 2>&1 || install_python
verify_python
if ! python3 -m venv .venv 2>/dev/null && [ ! -x .venv/bin/python ]; then
  install_python
  python3 -m venv .venv
fi
PY="$ROOT/.venv/bin/python"
[ -f .env ] || cp .env.example .env
mkdir -p .aeris/state .aeris/knowledge .aeris/ingress .aeris/installers data logs

if [ "${AERIS_SKIP_CORE_SYNC:-0}" != "1" ]; then
  if [ -d "$ROOT/portable_assets/core-reference" ] && [ ! -d "$ROOT/.aeris/core-reference" ]; then
    echo 'Restoring staged read-only Core reference...'
    cp -a "$ROOT/portable_assets/core-reference" "$ROOT/.aeris/core-reference"
  elif command -v git >/dev/null 2>&1; then
    "$ROOT/scripts/sync-core.sh" || echo 'WARNING: Core refresh failed; cached/staged Core will be used if present.' >&2
  else
    echo 'WARNING: Git unavailable; offline install requires portable_assets/core-reference.' >&2
  fi
fi

if ! command -v ollama >/dev/null 2>&1; then
  STAGED="$ROOT/portable_assets/installers/ollama-install.sh"
  INSTALLER="$ROOT/.aeris/installers/ollama-install.sh"
  if [ -f "$STAGED" ]; then
    command -v sha256sum >/dev/null 2>&1 || { echo 'sha256sum is required for staged installer verification.' >&2; exit 3; }
    verify_staged_hash "$STAGED"
    cp "$STAGED" "$INSTALLER"
    echo 'Using checksum-verified staged Ollama installer.'
  else
    echo 'Ollama not found; downloading exact official HTTPS installer URL...'
    if command -v curl >/dev/null 2>&1; then curl -fsSL https://ollama.com/install.sh -o "$INSTALLER";
    elif command -v wget >/dev/null 2>&1; then wget -q https://ollama.com/install.sh -O "$INSTALLER";
    else install_python; curl -fsSL https://ollama.com/install.sh -o "$INSTALLER"; fi
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum "$INSTALLER" | tee "$INSTALLER.sha256"
    fi
    printf '{"source":"https://ollama.com/install.sh","integrity":"TLS transport + recorded SHA-256; not a pinned upstream signature","downloaded_at":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$INSTALLER.provenance.json"
  fi
  chmod +x "$INSTALLER"
  bash "$INSTALLER"
fi

if command -v ollama >/dev/null 2>&1 && [ "${AERIS_SKIP_MODEL_PULL:-0}" != "1" ]; then
  if ! ollama list >/dev/null 2>&1; then
    if command -v systemctl >/dev/null 2>&1; then run_root systemctl start ollama 2>/dev/null || true; fi
    if ! ollama list >/dev/null 2>&1; then nohup ollama serve > .aeris/state/ollama.log 2>&1 & sleep 4; fi
  fi
  ollama pull "$MODEL"
fi

"$PY" -m aeris_runtime mode set "$MODE"
"$PY" -m aeris_runtime machine detect --write
"$PY" -m aeris_runtime knowledge build
"$PY" -m unittest discover -s tests -v
"$PY" -m aeris_runtime company status
set +e
"$PY" -m aeris_runtime doctor
doctor=$?
set -e
if [ "${AERIS_SKIP_MODEL_PULL:-0}" != "1" ] && [ "$doctor" -ne 0 ]; then
  echo "AERIS local continuity verification failed (doctor exit $doctor)." >&2
  exit "$doctor"
fi
[ "$doctor" -eq 0 ] || echo "WARNING: installed with limits because model installation was explicitly skipped (doctor exit $doctor)." >&2
echo 'AERIS bootstrap finished.'
echo 'Next: run scripts/local-acceptance.sh before declaring this machine VERIFIED.'
