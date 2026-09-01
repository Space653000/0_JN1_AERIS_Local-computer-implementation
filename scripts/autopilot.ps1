param(
  [ValidateSet('auto','offline','local','cloud')][string]$Mode='auto',
  [string]$LocalModel='qwen3:4b-instruct',
  [switch]$HardOffline,
  [switch]$CISmoke,
  [switch]$NoSupervisor
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$State=Join-Path $Root '.aeris\state'
$Preflight=Join-Path $State 'AUTOPILOT_PREFLIGHT.json'
$Result=Join-Path $State 'AUTOPILOT_RESULT.json'
$Started=(Get-Date).ToUniversalTime().ToString('o')
$Stage='SAFE_PREFLIGHT'
$Py=$null
$OriginalLocation=Get-Location

function Write-JsonFile($Path,$Payload){
  New-Item -ItemType Directory -Force -Path (Split-Path $Path -Parent) | Out-Null
  $Payload | ConvertTo-Json -Depth 12 | Set-Content -Path $Path -Encoding utf8
}
function Git-Value([string[]]$GitArgs){
  try { return ((& git -C $Root @GitArgs 2>$null) -join "`n").Trim() } catch { return '' }
}
function Resolve-AerisPython {
  $venv=Join-Path $Root '.venv\Scripts\python.exe'
  if(Test-Path $venv){ return $venv }
  $cmd=Get-Command python -ErrorAction SilentlyContinue
  if($cmd){ return $cmd.Source }
  return $null
}
function Write-FinalResult($Status,$Opening,$Failure){
  $ImplSha=Git-Value @('rev-parse','HEAD')
  $CoreSha='UNKNOWN'
  try { $CoreSha=(Get-Content (Join-Path $Root 'core.lock.json') -Raw | ConvertFrom-Json).baseline_sha } catch {}
  $Machine=$null
  if($Py){ try { $Machine=((& $Py -m aeris_runtime machine detect) -join "`n") | ConvertFrom-Json } catch {} }
  $Unattended=$null
  try { $Unattended=Get-Content (Join-Path $State 'UNATTENDED_INSTALL.json') -Raw | ConvertFrom-Json } catch {}
  $Payload=[ordered]@{
    schema_version=2
    run_kind=($(if($CISmoke){'CI_SMOKE'}else{'REAL_AUTOPILOT'}))
    result=$Status
    started_at_utc=$Started
    finished_at_utc=(Get-Date).ToUniversalTime().ToString('o')
    local_target_path=$Root
    canonical_core_sha=$CoreSha
    implementation_sha=$ImplSha
    requested_mode=$Mode
    requested_local_model=$LocalModel
    hard_offline_requested=[bool]$HardOffline
    machine_profile=$(if($Machine){$Machine.profile}else{'UNKNOWN'})
    company_opening_state=$(if($Opening){$Opening.operational_state}else{'NOT_OPENED'})
    company_complete=$false
    supervisor=$(if($Opening -and $Opening.PSObject.Properties.Name -contains 'supervisor'){$Opening.supervisor}else{$null})
    unattended_operations=$Unattended
    failure=$Failure
    evidence_paths=[ordered]@{
      preflight=$Preflight
      deployment=(Join-Path $State 'DEPLOYMENT_REPORT.json')
      local_acceptance=(Join-Path $State 'LOCAL_ACCEPTANCE.json')
      company_opening=(Join-Path $State 'COMPANY_OPENING.json')
      heartbeat=(Join-Path $State 'HEARTBEAT.json')
      unattended_install=(Join-Path $State 'UNATTENDED_INSTALL.json')
      unattended_runtime=(Join-Path $State 'UNATTENDED_OPERATIONS.json')
      audit=(Join-Path $Root '.aeris\audit\audit.jsonl')
    }
    truth='Autopilot completion means the supported local control plane was deployed/opened for its verified scope. It never means every acoustic capability, proprietary tool or release gate is complete.'
  }
  Write-JsonFile $Result $Payload
}

try {
  Set-Location $Root
  New-Item -ItemType Directory -Force -Path $State | Out-Null
  $GitPresent=[bool](Get-Command git -ErrorAction SilentlyContinue)
  $Remote=$(if($GitPresent){Git-Value @('remote','get-url','origin')}else{''})
  $Dirty=$(if($GitPresent){Git-Value @('status','--porcelain','--untracked-files=no')}else{''})
  $Drive=Get-PSDrive -Name ([IO.Path]::GetPathRoot($Root).TrimEnd('\').TrimEnd(':')) -ErrorAction SilentlyContinue
  $PreflightPayload=[ordered]@{
    schema_version=1
    status='BOOTSTRAPPING'
    assessed_at_utc=(Get-Date).ToUniversalTime().ToString('o')
    local_target_path=$Root
    os=[System.Environment]::OSVersion.VersionString
    architecture=[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
    git_present=$GitPresent
    implementation_origin=$Remote
    versioned_worktree_dirty=[bool]$Dirty
    versioned_worktree_detail=$Dirty
    free_disk_gb=$(if($Drive){[math]::Round($Drive.Free/1GB,2)}else{$null})
    requested_mode=$Mode
    local_model=$LocalModel
    hard_offline_requested=[bool]$HardOffline
    ci_smoke=[bool]$CISmoke
    safety='No destructive workspace reset, no Core auto-drift acceptance, no license/credential invention.'
  }
  Write-JsonFile $Preflight $PreflightPayload

  if($GitPresent -and $Remote -and $Remote -notmatch 'Space653000/0_JN1_AERIS_Local-computer-implementation(?:\.git)?$'){
    throw "BLOCKED_WRONG_IMPLEMENTATION_ORIGIN: $Remote"
  }
  if($Dirty){
    throw 'BLOCKED_VERSIONED_WORKTREE_DIRTY: preserve/review tracked local changes before zero-touch deployment; Autopilot will not hide or overwrite them.'
  }

  $Stage='INSTALL_CONFIGURE'
  if($CISmoke){
    & (Join-Path $Root 'INSTALL_AERIS_LOCAL.ps1') -Mode $Mode -LocalModel $LocalModel -SkipLocalModelInstall -SkipCoreSync
  } else {
    & (Join-Path $Root 'INSTALL_AERIS_LOCAL.ps1') -Mode $Mode -LocalModel $LocalModel
  }
  if($LASTEXITCODE -ne 0){ throw "Installer failed with exit $LASTEXITCODE" }
  $Py=Resolve-AerisPython
  if(-not $Py){ throw 'AERIS Python runtime unavailable after installer.' }

  $Stage='P0_TRUST_BASELINE'
  & $Py -m aeris_runtime audit verify | Out-Host
  if($LASTEXITCODE -ne 0){ throw 'Audit ledger integrity verification failed.' }

  if($CISmoke){
    $Stage='CI_SMOKE_ONLY'
    & $Py -m unittest discover -s tests -v
    if($LASTEXITCODE -ne 0){ throw 'CI Autopilot unit/security tests failed.' }
    & $Py -m aeris_runtime company status | Out-Host
    if($LASTEXITCODE -ne 0){ throw 'CI Autopilot company manifest check failed.' }
    & (Join-Path $Root 'scripts\install-unattended-windows.ps1') -CISmoke
    if($LASTEXITCODE -ne 0){ throw 'CI unattended-operations smoke failed.' }
    Write-FinalResult 'CI_SMOKE_PASS_NOT_REAL_OPENING' $null $null
    Write-Host "AERIS Autopilot CI smoke PASS. No real-machine acceptance or company opening was claimed. Report: $Result" -ForegroundColor Green
    exit 0
  }

  $Stage='REAL_MACHINE_ACCEPTANCE'
  try {
    if($HardOffline){
      & (Join-Path $Root 'scripts\local-acceptance.ps1') -HardOffline
    } else {
      & (Join-Path $Root 'scripts\local-acceptance.ps1')
    }
    if($LASTEXITCODE -ne 0){ throw "Real-machine acceptance failed with exit $LASTEXITCODE" }
  } finally {
    if($Py){ & $Py -m aeris_runtime mode set $Mode | Out-Host }
  }

  $Stage='COMPANY_OPENING'
  $OpenArgs=@('-m','aeris_runtime','company','open','--actor','Codex Autopilot')
  if(-not $NoSupervisor){ $OpenArgs += @('--start-supervisor','--port','8765') }
  $OpeningText=(& $Py @OpenArgs) -join "`n"
  $OpenExit=$LASTEXITCODE
  $Opening=$OpeningText | ConvertFrom-Json
  if($OpenExit -ne 0 -or $Opening.operational_state -eq 'BLOCKED'){
    throw "Company opening blocked: $($Opening.blockers -join ', ')"
  }
  if($Opening.operational_state -ne 'OPEN_VERIFIED_SCOPE'){
    throw "Real Autopilot acceptance passed but opening did not reach OPEN_VERIFIED_SCOPE; observed $($Opening.operational_state)"
  }

  if(-not $NoSupervisor){
    $Stage='UNATTENDED_OPERATIONS'
    & (Join-Path $Root 'scripts\install-unattended-windows.ps1') -Port 8765 -IntervalSec 20
    if($LASTEXITCODE -ne 0){ throw 'Persistent unattended operations could not be registered. This is a real OS-policy/admin Human Gate.' }
  }

  $Stage='EVIDENCE_HANDOFF'
  Write-FinalResult 'PASS_OPEN_VERIFIED_SCOPE' $Opening $null
  Write-Host ''
  Write-Host 'AERIS local company control plane is OPEN for the verified scope and unattended continuity has been registered.' -ForegroundColor Green
  Write-Host "Autopilot report: $Result"
  Write-Host 'External licensed tools, physical calibration and formal R3/R4 release remain real Human/External gates.'
  exit 0
}
catch {
  $Failure=[ordered]@{stage=$Stage;message=$_.Exception.Message;type=$_.Exception.GetType().FullName}
  if($Py){ try { & $Py -m aeris_runtime mode set $Mode *> $null } catch {} }
  Write-FinalResult 'BLOCKED_OR_FAILED' $null $Failure
  Write-Error "AERIS Autopilot stopped at ${Stage}: $($_.Exception.Message). Evidence: $Result"
  exit 20
}
finally {
  Set-Location $OriginalLocation
}
