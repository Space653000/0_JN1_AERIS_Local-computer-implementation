#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
CI_SMOKE=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --ci-smoke) CI_SMOKE=1; shift ;;
    -h|--help) echo 'Usage: CLAUDE_VERIFY_AERIS.sh [--ci-smoke]'; exit 0 ;;
    *) echo "Unknown Claude verification argument: $1" >&2; exit 2 ;;
  esac
done

PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo 'Claude verification requires an existing AERIS Python runtime. It does not install or repair by default.' >&2; exit 21; }
STATE="$ROOT/.aeris/state"
mkdir -p "$STATE"
TESTS_REPORT="$STATE/CLAUDE_TESTS.json"
TESTS_LOG="$STATE/claude-unit-tests.log"
DRIFT_LOG="$STATE/claude-core-drift.log"
REVIEW_LOG="$STATE/claude-review.log"

echo '=== AERIS Independent Claude Acceptance ==='
echo 'Mode: review only. No install, silent repair, Core write, or gate bypass.'

set +e
"$PY" -m unittest discover -s tests -v 2>&1 | tee "$TESTS_LOG"
unit_code=${PIPESTATUS[0]}
"$PY" scripts/check-core-drift.py 2>&1 | tee "$DRIFT_LOG"
drift_code=${PIPESTATUS[0]}
set -e
[ "$unit_code" -eq 0 ] && unit_result='PASS' || unit_result='FAIL'
if [ "$drift_code" -eq 0 ]; then drift='PASS'; elif [ "$drift_code" -eq 4 ]; then drift='FAIL'; else drift='NOT_TESTED'; fi

"$PY" - "$TESTS_REPORT" "$unit_result" "$unit_code" "$drift" "$drift_code" "$TESTS_LOG" <<'PYCODE'
import datetime,json,sys
path,result,unit_code,drift,drift_code,log=sys.argv[1:]
payload={
 'schema_version':1,'reviewer':'Claude Code','result':result,'unit_test_exit_code':int(unit_code),
 'remote_core_drift_gate':drift,'remote_core_drift_exit_code':int(drift_code),
 'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'unit_test_log':log,
 'truth':'PASS means deterministic repository tests passed. Remote Core drift NOT_TESTED means live GitHub comparison was unavailable and remains a review limitation.'}
open(path,'w',encoding='utf-8').write(json.dumps(payload,indent=2)+'\n')
PYCODE

if [ "$CI_SMOKE" -eq 1 ]; then
  if [ "$unit_code" -eq 0 ] && [ "$drift" = 'PASS' ]; then
    echo 'Claude verification CI smoke PASS. This does not validate a real local deployment.'
    exit 0
  fi
  echo "Claude verification CI smoke failed: unit=$unit_result core_drift=$drift" >&2
  exit 22
fi

# Repeatable read/verification checks; do not repair failures in this acceptance pass.
"$PY" -m aeris_runtime company status || true
"$PY" -m aeris_runtime core verify || true
"$PY" -m aeris_runtime audit verify || true
"$PY" -m aeris_runtime doctor || true

set +e
review_text="$("$PY" -m aeris_runtime review --reviewer 'Claude Code' 2>&1)"
review_code=$?
set -e
printf '%s\n' "$review_text" | tee "$REVIEW_LOG"
final="$(printf '%s' "$review_text" | "$PY" -c 'import json,sys; print(json.load(sys.stdin).get("final_result","UNPARSEABLE"))' 2>/dev/null || echo UNPARSEABLE)"
case "$final" in
  PASS|PASS_WITH_LIMITS)
    echo "Claude independent acceptance: $final"
    exit 0 ;;
  UNPARSEABLE)
    echo "Claude deterministic review output could not be parsed. See $REVIEW_LOG" >&2
    exit 23 ;;
  *)
    echo "Claude independent acceptance: $final. See $ROOT/.aeris/state/CLAUDE_ACCEPTANCE.json" >&2
    [ "$review_code" -ne 0 ] && exit "$review_code"
    exit 24 ;;
esac
