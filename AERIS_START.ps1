param([int]$Port=8765)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$Python=Join-Path $Root '.venv\Scripts\python.exe'
if(-not (Test-Path $Python)){
  $cmd=Get-Command python -ErrorAction SilentlyContinue
  if(-not $cmd){ throw 'Python runtime not found. Run AERIS_AUTOPILOT.ps1 first.' }
  $Python=$cmd.Source
}
Set-Location $Root

Write-Host '=== AERIS 本機系統啟動 / Starting AERIS Local System ===' -ForegroundColor Cyan
$listening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($conn in $listening) {
  try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop } catch {}
}
Start-Sleep -Seconds 1
Start-Process -FilePath $Python -ArgumentList '-m','aeris_runtime','company','open','--actor','AERIS_START','--start-supervisor','--port',"$Port" -WindowStyle Hidden

Write-Host '等待後端伺服器啟動 / Waiting for the backend to come up...' -ForegroundColor Cyan
$health = $null
for ($i = 0; $i -lt 30 -and -not $health; $i++) {
  Start-Sleep -Seconds 1
  try { $health = (& $Python -c "import urllib.request,json; print(json.load(urllib.request.urlopen('http://127.0.0.1:$Port/health',timeout=2))['implementation_sha'])" 2>$null) } catch {}
}
if (-not $health) {
  Write-Warning '後端伺服器 30 秒內未能啟動 / Backend did not come up within 30s.'
  exit 1
}

Write-Host '重新驗證全公司工程進度（確保點檢表反映真實狀態）/ Refreshing full company progress Evidence...' -ForegroundColor Cyan
& $Python -m aeris_runtime.progress_verify
$verifyExit = $LASTEXITCODE

Write-Host ''
& $Python (Join-Path $Root 'scripts\aeris_launch_checklist.py') "$Port"
$checklistExit = $LASTEXITCODE

if ($checklistExit -eq 0) {
  Write-Host ''
  Write-Host '系統已就緒，開啟瀏覽器 / System ready, opening browser...' -ForegroundColor Green
  Start-Process "http://127.0.0.1:$Port/dashboard"
} else {
  Write-Host ''
  Write-Warning '有項目未通過點檢，請檢查上方訊息再開啟瀏覽器 / Some checks failed -- review the output above before relying on the UI.'
}

exit $checklistExit
