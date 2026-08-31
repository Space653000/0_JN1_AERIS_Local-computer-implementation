#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo 'Python not found. Run INSTALL_AERIS_LOCAL.sh first.' >&2; exit 2; }
REPORT="$ROOT/.aeris/state/LOCAL_ACCEPTANCE.json"
mkdir -p "$(dirname "$REPORT")"

echo '=== AERIS Real-Machine Acceptance ==='
"$PY" -m aeris_runtime company status
"$PY" -m unittest discover -s tests -v
"$PY" -m aeris_runtime knowledge build

CORE="$ROOT/.aeris/core-reference"
[ -d "$CORE/.git" ] || { echo 'FAIL: read-only Core cache is missing. Sync online or stage portable_assets/core-reference.' >&2; exit 3; }
PUSH_URL="$(git -C "$CORE" remote get-url --push origin 2>/dev/null || true)"
case "$PUSH_URL" in DISABLED://*) ;; *) echo "FAIL: Core push URL is not disabled: $PUSH_URL" >&2; exit 3;; esac
[ -x "$CORE/.git/hooks/pre-push" ] || { echo 'FAIL: Core deny pre-push hook is missing.' >&2; exit 3; }

"$PY" -m aeris_runtime mode set local
"$PY" -m aeris_runtime doctor
LOCAL_OUT="$ROOT/.aeris/state/local-inference.txt"
"$PY" -m aeris_runtime chat 'Reply briefly: AERIS local inference acceptance test.' > "$LOCAL_OUT"
[ -s "$LOCAL_OUT" ] || { echo 'FAIL: local inference returned no output.' >&2; exit 4; }

"$PY" -m aeris_runtime mode set offline
"$PY" -m aeris_runtime doctor
OFFLINE_OUT="$ROOT/.aeris/state/offline-inference.txt"
"$PY" -m aeris_runtime chat 'Reply briefly: AERIS offline-mode inference acceptance test.' > "$OFFLINE_OUT"
[ -s "$OFFLINE_OUT" ] || { echo 'FAIL: offline-mode inference returned no output.' >&2; exit 4; }

NETWORK_STATE='NOT_TESTED'
if [ "${AERIS_HARD_OFFLINE:-0}" = "1" ]; then
  if "$PY" - <<'PY'
import socket
try:
    s=socket.create_connection(('1.1.1.1',443),timeout=3); s.close(); raise SystemExit(0)
except OSError:
    raise SystemExit(1)
PY
  then
    echo 'FAIL: AERIS_HARD_OFFLINE=1 but external network is still reachable.' >&2
    exit 5
  else
    NETWORK_STATE='EXTERNAL_NETWORK_UNREACHABLE'
  fi
fi

"$PY" - "$REPORT" "$NETWORK_STATE" <<'PY'
import datetime,json,platform,sys
path,network=sys.argv[1:]
payload={
  'result':'PASS',
  'scope':'REAL_MACHINE_APPLICATION_ACCEPTANCE',
  'hard_offline_network_state':network,
  'platform':platform.platform(),
  'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'checks':['company_manifest','unit_tests','knowledge_build','core_read_only_guard','local_doctor','real_local_inference','offline_mode_doctor','real_offline_mode_inference']
}
open(path,'w',encoding='utf-8').write(json.dumps(payload,indent=2)+'\n')
PY

echo "PASS: real-machine application acceptance. Report: $REPORT"
if [ "$NETWORK_STATE" = 'NOT_TESTED' ]; then
  echo 'NOTE: Hard offline network isolation is NOT verified. Disconnect/block external network and rerun: AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh'
fi
