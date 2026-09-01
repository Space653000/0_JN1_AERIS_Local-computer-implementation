param(
  [int]$Port = 8765,
  [int]$IntervalSec = 20,
  [switch]$CISmoke
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$StateDir=Join-Path $Root '.aeris\state'
$Report=Join-Path $StateDir 'UNATTENDED_INSTALL.json'
$TaskName='AERIS-Local-Company-Watchdog'
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Write-Report($Status,$Mechanism,$Detail,$Verified){
  [ordered]@{
    schema_version=1
    platform='windows'
    status=$Status
    persistence_mechanism=$Mechanism
    detail=$Detail
    verified=[bool]$Verified
    autostart_scope='CURRENT_USER_LOGON'
    crash_recovery='watchdog loop + Scheduled Task restart when ScheduledTasks mechanism is available'
    task_name=$TaskName
    target_path=$Root
    assessed_at_utc=(Get-Date).ToUniversalTime().ToString('o')
    human_gate=$(if($Status -eq 'BLOCKED'){'ADMIN_OR_OS_POLICY_IF_PERSISTENCE_REGISTRATION_DENIED'}else{$null})
    truth='Current-user logon autostart is not pre-login SYSTEM service operation. Proprietary tool/license/hardware gates remain separate.'
  } | ConvertTo-Json -Depth 8 | Set-Content -Path $Report -Encoding utf8
}

$Py=Join-Path $Root '.venv\Scripts\python.exe'
if(-not (Test-Path $Py)){
  $cmd=Get-Command python -ErrorAction SilentlyContinue
  if($cmd){$Py=$cmd.Source}else{Write-Report 'BLOCKED' 'NONE' 'Python runtime unavailable' $false; exit 20}
}

if($CISmoke){
  & $Py -m aeris_runtime.watchdog --help *> $null
  if($LASTEXITCODE -ne 0){ throw 'Watchdog module entrypoint failed.' }
  Write-Report 'CI_SMOKE_PASS_NOT_REGISTERED' 'CI_SMOKE' 'Watchdog entrypoint and PowerShell syntax validated; OS persistence intentionally not changed in CI.' $false
  exit 0
}

try {
  Import-Module ScheduledTasks -ErrorAction Stop
  $Action=New-ScheduledTaskAction -Execute $Py -Argument "-m aeris_runtime.watchdog --port $Port --interval $IntervalSec" -WorkingDirectory $Root
  $Trigger=New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $Settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
  $Principal=New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description 'AERIS local-company watchdog; loopback service continuity only.' -Force | Out-Null
  $Before=Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
  $StartDisposition='START_REQUESTED'
  if($Before.State -eq 'Running'){
    $StartDisposition='ALREADY_RUNNING_NO_DUPLICATE_START'
  } else {
    Start-ScheduledTask -TaskName $TaskName
  }
  Start-Sleep -Seconds 2
  $Task=Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
  $Info=Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
  $ResultHex=('0x{0:X8}' -f ([uint32]$Info.LastTaskResult))
  $HealthyState=($Task.State -eq 'Running')
  $Status=$(if($HealthyState){'REGISTERED_RUNNING'}else{'REGISTERED_NOT_RUNNING'})
  Write-Report $Status 'WINDOWS_SCHEDULED_TASK' "State=$($Task.State); LastTaskResult=$ResultHex; StartDisposition=$StartDisposition. LastTaskResult is historical exit evidence and is not normalized to success while the watchdog is not Running." $HealthyState
  exit 0
}
catch {
  Write-Report 'BLOCKED' 'NONE' "ScheduledTasks failed: $($_.Exception.Message). No Startup-folder fallback was written because AERIS local-only scope forbids files outside the installation root." $false
  exit 20
}
