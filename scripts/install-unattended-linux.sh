#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT=8765
INTERVAL=20
CI_SMOKE=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --port) PORT="${2:?--port requires value}"; shift 2 ;;
    --interval) INTERVAL="${2:?--interval requires value}"; shift 2 ;;
    --ci-smoke) CI_SMOKE=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
STATE="$ROOT/.aeris/state"
REPORT="$STATE/UNATTENDED_INSTALL.json"
mkdir -p "$STATE"
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
[ -n "$PY" ] || { printf '{"schema_version":1,"status":"BLOCKED","detail":"Python unavailable"}\n' > "$REPORT"; exit 20; }

write_report(){
  local status="$1" mechanism="$2" detail="$3" verified="$4"
  "$PY" - "$REPORT" "$status" "$mechanism" "$detail" "$verified" "$ROOT" <<'PY'
import datetime,json,pathlib,sys
out,status,mechanism,detail,verified,root=sys.argv[1:]
payload={
  'schema_version':1,'platform':'linux_or_jetson','status':status,
  'persistence_mechanism':mechanism,'detail':detail,'verified':verified=='true',
  'autostart_scope':'USER_SESSION_OR_USER_LINGER_IF_CONFIGURED',
  'crash_recovery':'systemd Restart=always when systemd user service is available; fallback loop is weaker',
  'target_path':root,'assessed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'human_gate':'OS_POLICY_OR_LOGIN_LINGER_IF_HEADLESS_PRELOGIN_REQUIRED' if status=='REGISTERED_WITH_LIMITS' else None,
  'truth':'User systemd persistence does not prove pre-login boot service. Proprietary tool/license/hardware gates remain separate.'}
pathlib.Path(out).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
PY
}

if [ "$CI_SMOKE" = 1 ]; then
  "$PY" -m aeris_runtime.watchdog --help >/dev/null
  write_report 'CI_SMOKE_PASS_NOT_REGISTERED' 'CI_SMOKE' 'Watchdog entrypoint and shell syntax validated; OS persistence intentionally not changed in CI.' false
  exit 0
fi

if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
  UNIT_DIR="$HOME/.config/systemd/user"
  UNIT="$UNIT_DIR/aeris-local-company-watchdog.service"
  mkdir -p "$UNIT_DIR"
  cat > "$UNIT" <<EOF
[Unit]
Description=AERIS Local Company Watchdog
After=default.target

[Service]
Type=simple
WorkingDirectory=$ROOT
ExecStart=$PY -m aeris_runtime.watchdog --port $PORT --interval $INTERVAL
Restart=always
RestartSec=5
TimeoutStopSec=20

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now aeris-local-company-watchdog.service
  if systemctl --user is-active --quiet aeris-local-company-watchdog.service; then
    write_report 'REGISTERED' 'SYSTEMD_USER_SERVICE' 'systemd user watchdog active; starts with user manager.' true
    exit 0
  fi
fi

FALLBACK="$STATE/aeris-watchdog-loop.sh"
cat > "$FALLBACK" <<EOF
#!/usr/bin/env bash
cd "$ROOT"
while true; do
  "$PY" -m aeris_runtime.watchdog --port "$PORT" --interval "$INTERVAL" || true
  sleep 5
done
EOF
chmod 700 "$FALLBACK"
if command -v crontab >/dev/null 2>&1; then
  MARK='# AERIS_LOCAL_COMPANY_WATCHDOG'
  EXISTING="$(crontab -l 2>/dev/null || true)"
  CLEANED="$(printf '%s\n' "$EXISTING" | grep -v 'AERIS_LOCAL_COMPANY_WATCHDOG' || true)"
  { printf '%s\n' "$CLEANED"; printf '@reboot nohup %q >/dev/null 2>&1 & %s\n' "$FALLBACK" "$MARK"; } | crontab -
  nohup "$FALLBACK" >/dev/null 2>&1 &
  write_report 'REGISTERED_WITH_LIMITS' 'CRONTAB_REBOOT_FALLBACK' 'systemd user service unavailable; reboot fallback installed. Crash recovery is provided by the wrapper loop but session/cron policy is machine-dependent.' false
  exit 0
fi

write_report 'BLOCKED' 'NONE' 'No usable systemd user manager or crontab persistence mechanism.' false
exit 20
