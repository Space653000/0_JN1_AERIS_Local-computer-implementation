param([switch]$SkipRestart)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py=Join-Path $Root '.venv\Scripts\python.exe'

if (-not $SkipRestart) {
  Write-Host '=== Restarting local supervisor to align implementation_sha with HEAD ===' -ForegroundColor Cyan
  $listening = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
  foreach ($conn in $listening) {
    try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop } catch {}
  }
  Start-Sleep -Seconds 1
  Start-Process -FilePath $Py -ArgumentList '-m','aeris_runtime','company','open','--actor','AERIS-Gate-Cycle','--start-supervisor','--port','8765' -WindowStyle Hidden
}

$health = $null
for ($i = 0; $i -lt 20 -and -not $health; $i++) {
  Start-Sleep -Seconds 1
  try { $health = (& $Py -c "import urllib.request,json; print(json.load(urllib.request.urlopen('http://127.0.0.1:8765/health',timeout=2))['implementation_sha'])" 2>$null) } catch {}
}
if (-not $health) { Write-Warning 'Supervisor did not come up within 20s.'; exit 1 }
$head = (& git -C $Root rev-parse HEAD).Trim()
if ($health.Trim() -ne $head) {
  Write-Warning "Supervisor implementation_sha ($health) does not match HEAD ($head)."
}

Write-Host '=== Re-running progress_verify against the (now aligned) running server ===' -ForegroundColor Cyan
& $Py -m aeris_runtime.progress_verify
$verifyExit = $LASTEXITCODE

Write-Host '=== Reading /api/v1/progress ===' -ForegroundColor Cyan
& $Py -c @"
import urllib.request, json
from pathlib import Path
token_path = Path(r'$Root') / '.aeris' / 'state' / '.supervisor-token'
headers = {}
if token_path.is_file():
    headers['X-AERIS-Supervisor-Token'] = token_path.read_text(encoding='utf-8-sig').strip()
d = json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765/api/v1/progress', headers=headers)).read().decode('utf-8'))
print('truth_state:', d['truth_state'])
print('truth_errors:', d['truth_errors'])
print('overall_percent:', d['overall_percent'])
print('phase_percent:', d['phase_percent'])
if d['truth_state'] == 'FAIL_CLOSED':
    raise SystemExit(1)
"@
$progressExit = $LASTEXITCODE

if ($progressExit -ne 0) {
  Write-Warning 'Progress endpoint is FAIL_CLOSED -- Evidence is likely stale relative to a commit made after the last verify. Commit, then re-run this script.'
  exit 1
}
Write-Host 'Gate cycle complete: server aligned, Evidence fresh, truth_state not FAIL_CLOSED.' -ForegroundColor Green
exit $verifyExit
