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
& $Python -m aeris_runtime company open --actor 'AERIS_START' --start-supervisor --port $Port
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }
Start-Process "http://127.0.0.1:$Port/"
