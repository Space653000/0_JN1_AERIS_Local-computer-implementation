#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
MODE="auto"
MODEL="${AERIS_LOCAL_MODEL:-qwen3:4b-instruct}"
HARD_OFFLINE=0
CI_SMOKE=0
NO_SUPERVISOR=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    auto|offline|local|cloud) MODE="$1"; shift ;;
    --mode) MODE="${2:?--mode requires auto|offline|local|cloud}"; shift 2 ;;
    --model) MODEL="${2:?--model requires a model tag}"; shift 2 ;;
    --hard-offline) HARD_OFFLINE=1; shift ;;
    --ci-smoke) CI_SMOKE=1; shift ;;
    --no-supervisor) NO_SUPERVISOR=1; shift ;;
    -h|--help)
      echo 'Usage: AERIS_AUTOPILOT.sh [auto|offline|local|cloud] [--model TAG] [--hard-offline] [--ci-smoke] [--no-supervisor]'
      exit 0 ;;
    *) echo "Unknown Autopilot argument: $1" >&2; exit 2 ;;
  esac
done
case "$MODE" in auto|offline|local|cloud) ;; *) echo "Unsupported mode: $MODE" >&2; exit 2;; esac

STATE="$ROOT/.aeris/state"
PREFLIGHT="$STATE/AUTOPILOT_PREFLIGHT.json"
RESULT="$STATE/AUTOPILOT_RESULT.json"
mkdir -p "$STATE"
STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
STAGE='SAFE_PREFLIGHT'
PY=''

cat > "$PREFLIGHT" <<EOF
{
  "schema_version": 1,
  "status": "BOOTSTRAPPING",
  "assessed_at_utc": "$STARTED",
  "platform": "linux_or_jetson_shell_pre_python",
  "requested_mode": "$MODE",
  "hard_offline_requested": $([ "$HARD_OFFLINE" = 1 ] && echo true || echo false),
  "ci_smoke": $([ "$CI_SMOKE" = 1 ] && echo true || echo false),
  "truth": "Full machine inventory is produced by AERIS after Python/runtime bootstrap. This preflight does not claim verification."
}
EOF

resolve_py(){
  if [ -x "$ROOT/.venv/bin/python" ]; then printf '%s' "$ROOT/.venv/bin/python"; return 0; fi
  command -v python3 2>/dev/null || true
}
restore_mode(){
  if [ -n "$PY" ] && [ -x "$PY" ]; then "$PY" -m aeris_runtime mode set "$MODE" >/dev/null 2>&1 || true; fi
}
write_result(){
  local status="$1" stage="$2" failure="${3:-}" opening_file="$STATE/COMPANY_OPENING.json" unattended="$STATE/UNATTENDED_INSTALL.json"
  if [ -n "$PY" ] && [ -x "$PY" ]; then
    "$PY" - "$RESULT" "$status" "$stage" "$failure" "$STARTED" "$MODE" "$MODEL" "$HARD_OFFLINE" "$CI_SMOKE" "$ROOT" "$opening_file" "$unattended" <<'PYCODE'
import datetime,json,pathlib,subprocess,sys
out,status,stage,failure,started,mode,model,hard,ci,root,opening_path,unattended_path=sys.argv[1:]
root=pathlib.Path(root)
def git(*args):
    try:return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
    except Exception:return 'UNKNOWN'
def read_json(path):
    try:return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))
    except Exception:return None
core=read_json(root/'core.lock.json') or {}
opening=read_json(opening_path); unattended=read_json(unattended_path)
payload={
 'schema_version':2,'run_kind':'CI_SMOKE' if ci=='1' else 'REAL_AUTOPILOT',
 'result':status,'stage':stage,'started_at_utc':started,
 'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'local_target_path':str(root),'canonical_core_sha':core.get('baseline_sha','UNKNOWN'),
 'implementation_sha':git('rev-parse','HEAD'),'requested_mode':mode,'requested_local_model':model,
 'hard_offline_requested':hard=='1','company_opening_state':opening.get('operational_state') if opening else 'NOT_OPENED',
 'company_complete':False,'unattended_operations':unattended,'failure':failure or None,
 'evidence_paths':{
   'preflight':str(root/'.aeris/state/AUTOPILOT_PREFLIGHT.json'),
   'deployment':str(root/'.aeris/state/DEPLOYMENT_REPORT.json'),
   'local_acceptance':str(root/'.aeris/state/LOCAL_ACCEPTANCE.json'),
   'company_opening':str(root/'.aeris/state/COMPANY_OPENING.json'),
   'heartbeat':str(root/'.aeris/state/HEARTBEAT.json'),
   'unattended_install':str(root/'.aeris/state/UNATTENDED_INSTALL.json'),
   'unattended_runtime':str(root/'.aeris/state/UNATTENDED_OPERATIONS.json'),
   'audit':str(root/'.aeris/audit/audit.jsonl')},
 'truth':'Autopilot completion means the supported local control plane was deployed/opened for its verified scope; never every acoustic capability/tool/release gate.'}
pathlib.Path(out).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
PYCODE
  else
    printf '{"schema_version":1,"result":"%s","stage":"%s","company_complete":false,"truth":"Python unavailable; no verified opening claimed."}\n' "$status" "$stage" > "$RESULT"
  fi
}
fail(){
  local message="$1"
  restore_mode
  write_result 'BLOCKED_OR_FAILED' "$STAGE" "$message"
  echo "AERIS Autopilot stopped at $STAGE: $message" >&2
  echo "Evidence: $RESULT" >&2
  exit 20
}

if command -v git >/dev/null 2>&1 && [ -d .git ]; then
  ORIGIN="$(git remote get-url origin 2>/dev/null || true)"
  case "$ORIGIN" in
    *Space653000/0_JN1_AERIS_Local-computer-implementation|*Space653000/0_JN1_AERIS_Local-computer-implementation.git) ;;
    '') ;;
    *) fail "BLOCKED_WRONG_IMPLEMENTATION_ORIGIN: $ORIGIN" ;;
  esac
  DIRTY="$(git status --porcelain --untracked-files=no)"
  [ -z "$DIRTY" ] || fail 'BLOCKED_VERSIONED_WORKTREE_DIRTY: Autopilot will not hide/overwrite tracked local changes.'
fi

STAGE='INSTALL_CONFIGURE'
set +e
if [ "$CI_SMOKE" = 1 ]; then
  AERIS_LOCAL_MODEL="$MODEL" AERIS_SKIP_CORE_SYNC=1 AERIS_SKIP_LOCAL_RUNTIME_INSTALL=1 bash "$ROOT/INSTALL_AERIS_LOCAL.sh" "$MODE"
else
  AERIS_LOCAL_MODEL="$MODEL" bash "$ROOT/INSTALL_AERIS_LOCAL.sh" "$MODE"
fi
install_code=$?
set -e
[ "$install_code" -eq 0 ] || fail "Installer failed with exit $install_code"
PY="$(resolve_py)"
[ -n "$PY" ] || fail 'AERIS Python runtime unavailable after installer.'

STAGE='P0_TRUST_BASELINE'
"$PY" -m aeris_runtime audit verify || fail 'Audit ledger integrity verification failed.'

if [ "$CI_SMOKE" = 1 ]; then
  STAGE='CI_SMOKE_ONLY'
  "$PY" -m unittest discover -s tests -v || fail 'CI Autopilot unit/security tests failed.'
  "$PY" -m aeris_runtime company status || fail 'CI Autopilot company manifest check failed.'
  bash "$ROOT/scripts/install-unattended-linux.sh" --ci-smoke || fail 'CI unattended-operations smoke failed.'
  write_result 'CI_SMOKE_PASS_NOT_REAL_OPENING' "$STAGE" ''
  echo "AERIS Autopilot CI smoke PASS. No real-machine acceptance or company opening was claimed. Report: $RESULT"
  exit 0
fi

STAGE='REAL_MACHINE_ACCEPTANCE'
set +e
if [ "$HARD_OFFLINE" = 1 ]; then
  AERIS_HARD_OFFLINE=1 bash "$ROOT/scripts/local-acceptance.sh"
else
  bash "$ROOT/scripts/local-acceptance.sh"
fi
accept_code=$?
set -e
restore_mode
[ "$accept_code" -eq 0 ] || fail "Real-machine acceptance failed with exit $accept_code"

STAGE='COMPANY_OPENING'
OPEN_ARGS=( -m aeris_runtime company open --actor 'Codex Autopilot' )
if [ "$NO_SUPERVISOR" = 0 ]; then OPEN_ARGS+=( --start-supervisor --port 8765 ); fi
set +e
OPENING_JSON="$("$PY" "${OPEN_ARGS[@]}")"
open_code=$?
set -e
[ "$open_code" -eq 0 ] || fail "Company opening command failed with exit $open_code"
OPENING_STATE="$(printf '%s' "$OPENING_JSON" | "$PY" -c 'import json,sys; print(json.load(sys.stdin).get("operational_state","UNKNOWN"))')"
[ "$OPENING_STATE" = 'OPEN_VERIFIED_SCOPE' ] || fail "Real acceptance passed but opening state is $OPENING_STATE"

if [ "$NO_SUPERVISOR" = 0 ]; then
  STAGE='UNATTENDED_OPERATIONS'
  bash "$ROOT/scripts/install-unattended-linux.sh" --port 8765 --interval 20 || fail 'Persistent unattended operations could not be registered. This is a real OS-policy/session Human Gate.'
fi

STAGE='EVIDENCE_HANDOFF'
write_result 'PASS_OPEN_VERIFIED_SCOPE' "$STAGE" ''
echo 'AERIS local company control plane is OPEN for the verified scope and unattended continuity has been registered.'
echo "Autopilot report: $RESULT"
echo 'External licensed tools, physical calibration and formal R3/R4 release remain real Human/External gates.'
