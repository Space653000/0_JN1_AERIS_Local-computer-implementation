param([switch]$HardOffline)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py=Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $Py)) { throw 'Python venv not found. Run INSTALL_AERIS_LOCAL.ps1 first.' }
$Report=Join-Path $Root '.aeris\state\LOCAL_ACCEPTANCE.json'
New-Item -ItemType Directory -Force -Path (Split-Path $Report -Parent) | Out-Null

Write-Host '=== AERIS Real-Machine Acceptance ===' -ForegroundColor Cyan
& $Py -m aeris_runtime company status
if ($LASTEXITCODE -ne 0) { throw 'Company manifest validation failed.' }
& $Py -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed.' }
& $Py -m aeris_runtime knowledge build
if ($LASTEXITCODE -ne 0) { throw 'Knowledge build failed.' }

$Core=Join-Path $Root '.aeris\core-reference'
if (-not (Test-Path (Join-Path $Core '.git'))) { throw 'Read-only Core cache missing. Sync online or stage portable_assets/core-reference.' }
$PushUrl=(git -C $Core remote get-url --push origin 2>$null).Trim()
if (-not $PushUrl.StartsWith('DISABLED://')) { throw "Core push URL is not disabled: $PushUrl" }
$Hook=Join-Path $Core '.git\hooks\pre-push'
if (-not (Test-Path $Hook)) { throw 'Core deny pre-push hook is missing.' }

& $Py -m aeris_runtime mode set local
& $Py -m aeris_runtime doctor
if ($LASTEXITCODE -ne 0) { throw 'Local doctor failed.' }
$LocalOut=Join-Path $Root '.aeris\state\local-inference.txt'
& $Py -m aeris_runtime chat 'Reply briefly: AERIS local inference acceptance test.' | Set-Content -Encoding utf8 $LocalOut
if ((Get-Item $LocalOut).Length -le 0) { throw 'Local inference returned no output.' }

& $Py -m aeris_runtime mode set offline
& $Py -m aeris_runtime doctor
if ($LASTEXITCODE -ne 0) { throw 'Offline-mode doctor failed.' }
$OfflineOut=Join-Path $Root '.aeris\state\offline-inference.txt'
& $Py -m aeris_runtime chat 'Reply briefly: AERIS offline-mode inference acceptance test.' | Set-Content -Encoding utf8 $OfflineOut
if ((Get-Item $OfflineOut).Length -le 0) { throw 'Offline-mode inference returned no output.' }

$NetworkState='NOT_TESTED'
if ($HardOffline) {
  $client=New-Object System.Net.Sockets.TcpClient
  try {
    $iar=$client.BeginConnect('1.1.1.1',443,$null,$null)
    $connected=$iar.AsyncWaitHandle.WaitOne(3000,$false) -and $client.Connected
  } finally { $client.Close() }
  if ($connected) { throw 'HardOffline requested but external network is still reachable.' }
  $NetworkState='EXTERNAL_NETWORK_UNREACHABLE'
}

$Payload=[ordered]@{
  result='PASS'
  scope='REAL_MACHINE_APPLICATION_ACCEPTANCE'
  hard_offline_network_state=$NetworkState
  platform=[System.Environment]::OSVersion.VersionString
  verified_at_utc=(Get-Date).ToUniversalTime().ToString('o')
  checks=@('company_manifest','unit_tests','knowledge_build','core_read_only_guard','local_doctor','real_local_inference','offline_mode_doctor','real_offline_mode_inference')
}
$Payload | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 $Report
Write-Host "PASS: real-machine application acceptance. Report: $Report" -ForegroundColor Green
if (-not $HardOffline) { Write-Warning 'Hard offline network isolation is NOT verified. Disconnect/block external network and rerun with -HardOffline.' }
