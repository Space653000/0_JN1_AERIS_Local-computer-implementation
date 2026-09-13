#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8765}"
PY="$ROOT/.venv/bin/python"
[[ -x "$PY" ]] || PY="$(command -v python3 || command -v python || true)"
[[ -n "$PY" ]] || { echo 'Python runtime not found. Run AERIS_AUTOPILOT.sh first.' >&2; exit 2; }
cd "$ROOT"

echo '=== AERIS 本機系統啟動 / Starting AERIS Local System ==='
pid="$(lsof -ti tcp:"$PORT" 2>/dev/null || true)"
[[ -n "$pid" ]] && kill -9 $pid 2>/dev/null || true
sleep 1
nohup "$PY" -m aeris_runtime company open --actor AERIS_START --start-supervisor --port "$PORT" >/dev/null 2>&1 &

echo '等待後端伺服器啟動 / Waiting for the backend to come up...'
health=""
for i in $(seq 1 30); do
  sleep 1
  health="$("$PY" -c "import urllib.request,json,sys
try:
    print(json.load(urllib.request.urlopen('http://127.0.0.1:$PORT/health',timeout=2))['implementation_sha'])
except Exception:
    sys.exit(1)" 2>/dev/null || true)"
  [[ -n "$health" ]] && break
done
if [[ -z "$health" ]]; then echo '後端伺服器 30 秒內未能啟動 / Backend did not come up within 30s.' >&2; exit 1; fi

echo '重新驗證全公司工程進度 / Refreshing full company progress Evidence...'
"$PY" -m aeris_runtime.progress_verify || true

echo
"$PY" "$ROOT/scripts/aeris_launch_checklist.py" "$PORT"
checklist_exit=$?

if [[ $checklist_exit -eq 0 ]]; then
  echo
  echo '系統已就緒 / System ready.'
  if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:$PORT/dashboard" >/dev/null 2>&1 || true
  fi
else
  echo
  echo '有項目未通過點檢，請檢查上方訊息 / Some checks failed -- review the output above.' >&2
fi
exit $checklist_exit
