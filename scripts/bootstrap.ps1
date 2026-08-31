param(
  [switch]$SkipCoreSync
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host '== AERIS Local Bootstrap ==' -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw 'Python 3.10+ is required and was not found in PATH.'
}

if (-not (Test-Path '.venv')) {
  python -m venv .venv
}

New-Item -ItemType Directory -Force -Path '.aeris/state','data','logs' | Out-Null
if (-not (Test-Path '.env')) {
  Copy-Item '.env.example' '.env'
  Write-Host 'Created .env from .env.example'
}

if (-not $SkipCoreSync -and (Get-Command git -ErrorAction SilentlyContinue)) {
  try {
    & (Join-Path $PSScriptRoot 'sync-core.ps1')
  } catch {
    Write-Warning "Core sync skipped/failed (offline is allowed): $($_.Exception.Message)"
  }
}

$Python = Join-Path $Root '.venv/Scripts/python.exe'
& $Python -m unittest discover -s tests -v
$testCode = $LASTEXITCODE
& $Python -m aeris_runtime doctor
$doctorCode = $LASTEXITCODE

Write-Host ''
Write-Host 'Bootstrap completed.' -ForegroundColor Green
Write-Host 'Run: .\scripts\run.ps1 mode local'
Write-Host 'Run: .\scripts\run.ps1 chat "hello"'
if ($testCode -ne 0) { exit $testCode }
if ($doctorCode -ne 0) {
  Write-Warning 'Doctor is not READY. This is expected until a local AI server/model is available.'
}
exit 0
