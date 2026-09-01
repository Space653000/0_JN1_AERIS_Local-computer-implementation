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
  Start-ScheduledTask -TaskName $TaskName
  Start-Sleep -Seconds 2
  $Task=Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
  $Info=Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
  Write-Report 'REGISTERED' 'WINDOWS_SCHEDULED_TASK' "State=$($Task.State); LastTaskResult=$($Info.LastTaskResult)" $true
  exit 0
}
catch {
  try {
    $Startup=[Environment]::GetFolderPath('Startup')
    if(-not $Startup){throw 'Startup folder unavailable'}
    $CmdFile=Join-Path $Startup 'AERIS-Local-Company-Watchdog.cmd'
    $PyW=Join-Path (Split-Path $Py -Parent) 'pythonw.exe'
    $Runner=$(if(Test-Path $PyW){$PyW}else{$Py})
    $CmdBody="@echo off`r`ncd /d `"$Root`"`r`nstart `"`" /min `"$Runner`" -m aeris_runtime.watchdog --port $Port --interval $IntervalSec`r`n"
    Set-Content -Path $CmdFile -Value $CmdBody -Encoding ASCII
    Start-Process -FilePath $Runner -ArgumentList @('-m','aeris_runtime.watchdog','--port',"$Port",'--interval',"$IntervalSec") -WorkingDirectory $Root -WindowStyle Hidden
    Write-Report 'REGISTERED_WITH_LIMITS' 'STARTUP_FOLDER_FALLBACK' "ScheduledTasks failed: $($_.Exception.Message). Current-user Startup fallback registered; OS-level restart of the watchdog itself is not guaranteed until next logon." $false
    exit 0
  }
  catch {
    Write-Report 'BLOCKED' 'NONE' $_.Exception.Message $false
    exit 20
  }
}
