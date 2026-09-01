param([switch]$CISmoke)
$ErrorActionPreference='Continue'
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$State=Join-Path $Root '.aeris\state'
$TestsReport=Join-Path $State 'CLAUDE_TESTS.json'
$TestsLog=Join-Path $State 'claude-unit-tests.log'
$ReviewLog=Join-Path $State 'claude-review.log'
New-Item -ItemType Directory -Force -Path $State | Out-Null
$Py=Join-Path $Root '.venv\Scripts\python.exe'
if(-not (Test-Path $Py)){
  $cmd=Get-Command python -ErrorAction SilentlyContinue
  if($cmd){$Py=$cmd.Source}else{ Write-Error 'Claude verification requires an existing AERIS Python runtime. It does not install or repair by default.'; exit 21 }
}

Write-Host '=== AERIS Independent Claude Acceptance ===' -ForegroundColor Cyan
Write-Host 'Mode: review only. No install, silent repair, Core write, or gate bypass.'

& $Py -m unittest discover -s tests -v *>&1 | Tee-Object -FilePath $TestsLog | Out-Host
$UnitCode=$LASTEXITCODE
$UnitResult=$(if($UnitCode -eq 0){'PASS'}else{'FAIL'})

& $Py scripts/check-core-drift.py *>&1 | Tee-Object -FilePath (Join-Path $State 'claude-core-drift.log') | Out-Host
$DriftCode=$LASTEXITCODE
if($DriftCode -eq 0){$Drift='PASS'}elseif($DriftCode -eq 4){$Drift='FAIL'}else{$Drift='NOT_TESTED'}

$TestPayload=[ordered]@{
  schema_version=1
  reviewer='Claude Code'
  result=$UnitResult
  unit_test_exit_code=$UnitCode
  remote_core_drift_gate=$Drift
  remote_core_drift_exit_code=$DriftCode
  reviewed_at_utc=(Get-Date).ToUniversalTime().ToString('o')
  unit_test_log=$TestsLog
  truth='PASS means deterministic repository tests passed. Remote Core drift NOT_TESTED means live GitHub comparison was unavailable and must remain a review limitation.'
}
$TestPayload | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 $TestsReport

if($CISmoke){
  if($UnitCode -eq 0 -and $Drift -eq 'PASS'){
    Write-Host 'Claude verification CI smoke PASS. This does not validate a real local deployment.' -ForegroundColor Green
    exit 0
  }
  Write-Error "Claude verification CI smoke failed: unit=$UnitResult core_drift=$Drift"
  exit 22
}

# Read-only/repeatable checks. Failures are preserved as evidence; final aggregation decides scope.
& $Py -m aeris_runtime company status | Out-Host
& $Py -m aeris_runtime core verify | Out-Host
& $Py -m aeris_runtime audit verify | Out-Host
& $Py -m aeris_runtime doctor | Out-Host

$ReviewText=(& $Py -m aeris_runtime review --reviewer 'Claude Code' 2>&1) -join "`n"
$ReviewCode=$LASTEXITCODE
$ReviewText | Set-Content -Encoding utf8 $ReviewLog
Write-Host $ReviewText

try {
  $Review=$ReviewText | ConvertFrom-Json
  $Final=$Review.final_result
} catch {
  Write-Error "Claude deterministic review output could not be parsed. See $ReviewLog"
  exit 23
}

if($Final -in @('PASS','PASS_WITH_LIMITS')){
  Write-Host "Claude independent acceptance: $Final" -ForegroundColor Green
  Write-Host "Evidence: $($Review.evidence_paths.tests); $($Review.evidence_paths.acceptance); $($Review.evidence_paths.opening)"
  exit 0
}
Write-Error "Claude independent acceptance: $Final. Failures=$($Review.failures -join ', ') Blockers=$($Review.blockers -join ', ')"
exit $(if($ReviewCode -ne 0){$ReviewCode}else{24})
