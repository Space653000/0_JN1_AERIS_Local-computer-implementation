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

MACHINE_JSON="$("$PY" -m aeris_runtime machine detect)"
SUPPORTED="$(printf '%s' "$MACHINE_JSON" | "$PY" -c 'import json,sys; print("1" if json.load(sys.stdin).get("supported_baseline") else "0")')"
PROFILE="$(printf '%s' "$MACHINE_JSON" | "$PY" -c 'import json,sys; print(json.load(sys.stdin).get("profile","UNKNOWN"))')"
[ "$SUPPORTED" = '1' ] || { echo "FAIL: no supported AERIS Machine Profile for this system ($PROFILE)." >&2; exit 3; }

"$PY" -m aeris_runtime core verify || { echo 'FAIL: canonical Core cache verification failed.' >&2; exit 3; }

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
PROBES_JSON='[]'
if [ "${AERIS_HARD_OFFLINE:-0}" = "1" ]; then
  set +e
  PROBES_JSON="$($PY - <<'PY'
import json,socket
probes=[]
targets=[('1.1.1.1',443,'ipv4'),('8.8.8.8',443,'ipv4'),('9.9.9.9',443,'ipv4'),('example.com',443,'dns+tcp'),('2606:4700:4700::1111',443,'ipv6')]
for host,port,kind in targets:
    reachable=False
    try:
        s=socket.create_connection((host,port),timeout=2.5); s.close(); reachable=True
    except OSError: pass
    probes.append({'host':host,'port':port,'kind':kind,'reachable':reachable})
print(json.dumps(probes))
raise SystemExit(5 if any(p['reachable'] for p in probes) else 0)
PY
  )"
  probe_code=$?
  set -e
  if [ "$probe_code" -ne 0 ]; then
    echo 'FAIL: AERIS_HARD_OFFLINE=1 but at least one outbound network probe succeeded.' >&2
    printf '%s\n' "$PROBES_JSON" >&2
    exit 5
  fi
  NETWORK_STATE='OUTBOUND_PROBES_BLOCKED_NOT_GLOBAL_PROOF'
fi

"$PY" - "$REPORT" "$NETWORK_STATE" "$PROFILE" "$PROBES_JSON" <<'PY'
import datetime,json,os,platform,sys
path,network,profile,probes=sys.argv[1:]
proxy={k:v for k,v in os.environ.items() if k.lower() in {'http_proxy','https_proxy','all_proxy'} and v}
payload={
  'result':'PASS',
  'scope':'REAL_MACHINE_APPLICATION_ACCEPTANCE',
  'hard_offline_network_state':network,
  'hard_offline_claim_boundary':'Probe success would fail acceptance; blocked probes are evidence of tested paths, not mathematical proof that every OS process/path can never egress.',
  'network_probes':json.loads(probes),
  'proxy_environment':proxy,
  'machine_profile':profile,
  'platform':platform.platform(),
  'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'checks':['company_manifest','unit_tests','knowledge_build','supported_machine_profile','core_cache_integrity','local_doctor','real_local_inference','offline_mode_doctor','real_offline_mode_inference']
}
if network!='NOT_TESTED': payload['checks'].append('multi_path_outbound_probe_block')
open(path,'w',encoding='utf-8').write(json.dumps(payload,indent=2)+'\n')
PY

echo "PASS: real-machine application acceptance. Report: $REPORT"
if [ "$NETWORK_STATE" = 'NOT_TESTED' ]; then
  echo 'NOTE: Hard offline network isolation is NOT verified. Disconnect/block external network and rerun: AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh'
fi
