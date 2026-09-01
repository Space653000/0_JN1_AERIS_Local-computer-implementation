param([switch]$HardOffline)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py=Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $Py)) { throw 'Python venv not found. Run INSTALL_AERIS_LOCAL.ps1 first.' }
$Report=Join-Path $Root '.aeris\state\LOCAL_ACCEPTANCE.json'
New-Item -ItemType Directory -Force -Path (Split-Path $Report -Parent) | Out-Null

function Test-TcpReachable($HostName,[int]$Port=443,[int]$TimeoutMs=2500){
  $client=New-Object System.Net.Sockets.TcpClient
  try {
    $iar=$client.BeginConnect($HostName,$Port,$null,$null)
    return ($iar.AsyncWaitHandle.WaitOne($TimeoutMs,$false) -and $client.Connected)
  } catch { return $false } finally { $client.Close() }
}

Write-Host '=== AERIS Real-Machine Acceptance ===' -ForegroundColor Cyan
& $Py -m aeris_runtime company status
if ($LASTEXITCODE -ne 0) { throw 'Company manifest validation failed.' }
& $Py -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed.' }
& $Py -m aeris_runtime knowledge build
if ($LASTEXITCODE -ne 0) { throw 'Knowledge build failed.' }

$MachineJson=& $Py -m aeris_runtime machine detect
if($LASTEXITCODE -ne 0){ throw 'Machine detection failed.' }
$Machine=$MachineJson | ConvertFrom-Json
if(-not $Machine.supported_baseline){ throw "No supported AERIS Machine Profile for this machine: $($Machine.os)/$($Machine.architecture)" }

& $Py -m aeris_runtime core verify
if ($LASTEXITCODE -ne 0) { throw 'Canonical Core cache verification failed. Use guarded git cache or a checksum-verified Core snapshot.' }

& $Py -m aeris_runtime mode set local
& $Py -m aeris_runtime doctor
if ($LASTEXITCODE -ne 0) { throw 'Local doctor failed.' }
$LocalOut=Join-Path $Root '.aeris\state\local-inference.txt'
& $Py -m aeris_runtime chat 'Reply briefly: AERIS local inference acceptance test.' | Set-Content -Encoding utf8 $LocalOut
if ($LASTEXITCODE -ne 0 -or (Get-Item $LocalOut).Length -le 0) { throw 'Local inference failed or returned no output.' }

& $Py -m aeris_runtime mode set offline
& $Py -m aeris_runtime doctor
if ($LASTEXITCODE -ne 0) { throw 'Offline-mode doctor failed.' }
$OfflineOut=Join-Path $Root '.aeris\state\offline-inference.txt'
& $Py -m aeris_runtime chat 'Reply briefly: AERIS offline-mode inference acceptance test.' | Set-Content -Encoding utf8 $OfflineOut
if ($LASTEXITCODE -ne 0 -or (Get-Item $OfflineOut).Length -le 0) { throw 'Offline-mode inference failed or returned no output.' }

$NetworkState='NOT_TESTED'
$NetworkProbes=@()
$ProxyVars=@('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy')
$ProxyConfig=@{}
foreach($name in $ProxyVars){ $v=[Environment]::GetEnvironmentVariable($name); if($v){ $ProxyConfig[$name]=$v } }
if ($HardOffline) {
  $targets=@(
    @{host='1.1.1.1';port=443;kind='ipv4'},
    @{host='8.8.8.8';port=443;kind='ipv4'},
    @{host='9.9.9.9';port=443;kind='ipv4'},
    @{host='example.com';port=443;kind='dns+tcp'},
    @{host='2606:4700:4700::1111';port=443;kind='ipv6'}
  )
  foreach($t in $targets){
    $reachable=Test-TcpReachable $t.host $t.port
    $NetworkProbes += [ordered]@{host=$t.host;port=$t.port;kind=$t.kind;reachable=$reachable}
    if($reachable){ throw "HardOffline requested but outbound network probe succeeded: $($t.host):$($t.port)" }
  }
  $NetworkState='OUTBOUND_PROBES_BLOCKED_NOT_GLOBAL_PROOF'
}

$Payload=[ordered]@{
  result='PASS'
  scope='REAL_MACHINE_APPLICATION_ACCEPTANCE'
  hard_offline_network_state=$NetworkState
  hard_offline_claim_boundary='Probe success would fail acceptance; blocked probes are evidence of tested paths, not mathematical proof that every OS process/path can never egress.'
  network_probes=$NetworkProbes
  proxy_environment=$ProxyConfig
  machine_profile=$Machine.profile
  machine_support_state=$Machine.support_state
  platform=[System.Environment]::OSVersion.VersionString
  verified_at_utc=(Get-Date).ToUniversalTime().ToString('o')
  checks=@('company_manifest','unit_tests','knowledge_build','supported_machine_profile','core_cache_integrity','local_doctor','real_local_inference','offline_mode_doctor','real_offline_mode_inference')
}
if($HardOffline){ $Payload.checks += 'multi_path_outbound_probe_block' }
$Payload | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $Report
Write-Host "PASS: real-machine application acceptance. Report: $Report" -ForegroundColor Green
if (-not $HardOffline) { Write-Warning 'Hard offline network isolation is NOT verified. Disconnect/block external network and rerun with -HardOffline.' }
