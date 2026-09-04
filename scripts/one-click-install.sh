#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-auto}"
MODEL="${AERIS_LOCAL_MODEL:-qwen3:4b-instruct}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo '=== AERIS One-Click Company Installer ==='
echo 'Privacy: AERIS private engineering is application-routed to loopback or explicit trusted-LAN AI; OS/network isolation still requires local verification.'

run_root(){ if [ "$(id -u)" -eq 0 ]; then "$@"; elif command -v sudo >/dev/null 2>&1; then sudo "$@"; else echo "Need administrator privilege for: $*" >&2; exit 2; fi; }
install_python(){
  if command -v apt-get >/dev/null 2>&1; then run_root apt-get update; run_root apt-get install -y python3 python3-venv python3-pip curl ca-certificates git;
  elif command -v dnf >/dev/null 2>&1; then run_root dnf install -y python3 python3-pip curl ca-certificates git;
  elif command -v yum >/dev/null 2>&1; then run_root yum install -y python3 python3-pip curl ca-certificates git;
  elif command -v pacman >/dev/null 2>&1; then run_root pacman -Sy --noconfirm python python-pip curl ca-certificates git;
  elif command -v zypper >/dev/null 2>&1; then run_root zypper --non-interactive install python3 python3-pip curl ca-certificates git;
  else echo 'No supported package manager found. See docs/ONE_CLICK_INSTALL.md.' >&2; exit 2; fi
}
python_ok(){ "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 9)' >/dev/null 2>&1; }
resolve_python(){
  local c
  for c in "$ROOT/portable_assets/python/bin/python3" python3.13 python3.12 python3.11 python3; do
    if [[ "$c" == /* ]]; then [ -x "$c" ] && python_ok "$c" && { echo "$c"; return 0; }
    elif command -v "$c" >/dev/null 2>&1 && python_ok "$(command -v "$c")"; then command -v "$c"; return 0; fi
  done
  return 1
}
verify_staged_hash(){
  local file="$1" sidecar="$1.sha256"
  [ -f "$sidecar" ] || { echo "Staged installer requires SHA-256 sidecar: $sidecar" >&2; exit 3; }
  command -v sha256sum >/dev/null 2>&1 || { echo 'sha256sum is required for staged asset verification.' >&2; exit 3; }
  local expected actual
  expected="$(awk '{print tolower($1)}' "$sidecar" | head -1)"
  actual="$(sha256sum "$file" | awk '{print tolower($1)}')"
  [ "$expected" = "$actual" ] || { echo "SHA-256 mismatch for staged installer: $file" >&2; exit 3; }
}
set_env_value(){
  local key="$1" value="$2"
  "$PY" - "$ROOT/.env" "$key" "$value" <<'PY'
from pathlib import Path
import sys
path,key,value=Path(sys.argv[1]),sys.argv[2],sys.argv[3]
lines=path.read_text(encoding='utf-8-sig').splitlines() if path.exists() else []
out=[]; found=False
for line in lines:
    if line.startswith(key+'='):
        out.append(key+'='+value); found=True
    else: out.append(line)
if not found: out.append(key+'='+value)
path.write_text('\n'.join(out)+'\n',encoding='utf-8')
PY
}
model_installed(){ command -v ollama >/dev/null 2>&1 && ollama show "$MODEL" >/dev/null 2>&1; }
install_staged_model(){
  local models="$ROOT/portable_assets/models" manifest="$ROOT/portable_assets/models/model.manifest.json"
  [ -f "$manifest" ] || return 1
  local model_name format file expected
  model_name="$($PY -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["model_name"])' "$manifest")"
  format="$($PY -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["format"])' "$manifest")"
  file="$($PY -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["file"])' "$manifest")"
  expected="$($PY -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["sha256"].lower())' "$manifest")"
  [ "$model_name" = "$MODEL" ] || { echo "Staged model is $model_name but requested model is $MODEL" >&2; exit 3; }
  [ "$format" = 'gguf' ] || { echo "Unsupported staged model format: $format (gguf required)." >&2; exit 3; }
  local model_file="$models/$file"
  [ -f "$model_file" ] || { echo "Staged model file missing: $model_file" >&2; exit 3; }
  local actual="$(sha256sum "$model_file" | awk '{print tolower($1)}')"
  [ "$actual" = "$expected" ] || { echo 'Staged model SHA-256 mismatch.' >&2; exit 3; }
  local modelfile="$ROOT/.aeris/installers/Modelfile.offline"
  printf 'FROM "%s"\n' "$model_file" > "$modelfile"
  echo "Importing checksum-verified staged GGUF model as $MODEL..."
  ollama create "$MODEL" -f "$modelfile"
}

PY="$(resolve_python || true)"
if [ -z "$PY" ]; then
  if [ "$MODE" = 'offline' ]; then
    echo 'Offline clean-machine Linux/Jetson install requires preinstalled Python >=3.10 or a machine-compatible portable_assets/python/bin/python3.' >&2
    exit 2
  fi
  install_python
  PY="$(resolve_python || true)"
fi
[ -n "$PY" ] || { echo 'Supported Python >=3.10 is still unavailable. This OS/distro is BLOCKED until a supported Python package/profile is supplied.' >&2; exit 2; }

if ! "$PY" -m venv .venv 2>/dev/null && [ ! -x .venv/bin/python ]; then
  [ "$MODE" != 'offline' ] || { echo 'Python venv support missing in offline mode; stage/install the distro-specific venv package first.' >&2; exit 2; }
  install_python
  "$PY" -m venv .venv
fi
PY="$ROOT/.venv/bin/python"
"$PY" -B "$ROOT/scripts/bootstrap-engineering.py" --mode "$MODE"
[ -f .env ] || cp .env.example .env
set_env_value AERIS_LOCAL_MODEL "$MODEL"
mkdir -p .aeris/state .aeris/knowledge .aeris/ingress .aeris/installers data logs

if [ "${AERIS_SKIP_CORE_SYNC:-0}" != "1" ]; then
  if [ -d "$ROOT/portable_assets/core-reference" ] && [ ! -d "$ROOT/.aeris/core-reference" ]; then
    echo 'Restoring staged read-only Core reference...'
    cp -a "$ROOT/portable_assets/core-reference" "$ROOT/.aeris/core-reference"
  elif command -v git >/dev/null 2>&1; then
    "$ROOT/scripts/sync-core.sh" || echo 'WARNING: Core refresh failed; cached/staged Core will be used if present.' >&2
  fi
  if [ ! -d "$ROOT/.aeris/core-reference" ]; then
    [ "$MODE" != 'offline' ] || { echo 'Offline install requires portable_assets/core-reference or an existing verified Core cache.' >&2; exit 3; }
    echo 'WARNING: Canonical Core cache is absent; local acceptance remains BLOCKED until Core is synchronized.' >&2
  fi
fi

if [ "${AERIS_SKIP_LOCAL_RUNTIME_INSTALL:-0}" != "1" ]; then
  if ! command -v ollama >/dev/null 2>&1; then
    STAGED="$ROOT/portable_assets/installers/ollama-install.sh"
    INSTALLER="$ROOT/.aeris/installers/ollama-install.sh"
    if [ "$MODE" = 'offline' ]; then
      echo 'BLOCKED: offline mode will not execute ollama-install.sh because it is a network/bootstrap installer, not a self-contained air-gap runtime package.' >&2
      echo 'Preinstall Ollama on this supported machine before disconnecting, or provide a future machine-specific self-contained runtime package after that package format is implemented and verified.' >&2
      exit 3
    elif [ -f "$STAGED" ]; then
      verify_staged_hash "$STAGED"
      cp "$STAGED" "$INSTALLER"
      echo 'Using checksum-verified staged Ollama bootstrap script in ONLINE mode. It may still fetch runtime assets.'
    else
      echo 'Ollama not found; downloading official HTTPS installer. This is transport-protected but NOT a pinned upstream signature.'
      if command -v curl >/dev/null 2>&1; then curl -fsSL https://ollama.com/install.sh -o "$INSTALLER";
      elif command -v wget >/dev/null 2>&1; then wget -q https://ollama.com/install.sh -O "$INSTALLER";
      else install_python; curl -fsSL https://ollama.com/install.sh -o "$INSTALLER"; fi
      if command -v sha256sum >/dev/null 2>&1; then sha256sum "$INSTALLER" | tee "$INSTALLER.sha256"; fi
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
    if ! model_installed; then
      if ! install_staged_model; then
        [ "$MODE" != 'offline' ] || { echo "Offline mode requires staged model assets for '$MODEL' or a preinstalled model." >&2; exit 3; }
        ollama pull "$MODEL"
      fi
    fi
  fi
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
if [ "${AERIS_SKIP_LOCAL_RUNTIME_INSTALL:-0}" != "1" ] && [ "${AERIS_SKIP_MODEL_PULL:-0}" != "1" ] && [ "$doctor" -ne 0 ]; then
  echo "AERIS local continuity verification failed (doctor exit $doctor)." >&2
  exit "$doctor"
fi
[ "$doctor" -eq 0 ] || echo "WARNING: installed with limits because local runtime/model verification was explicitly skipped (doctor exit $doctor)." >&2
echo 'AERIS bootstrap finished. INSTALLATION IS NOT THE SAME AS VERIFIED.'
echo 'Next: run scripts/local-acceptance.sh before declaring this machine VERIFIED.'
