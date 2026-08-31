param([ValidateSet('auto','offline','local','cloud')][string]$Mode = 'auto')
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Write-Host 'AERIS Portable Company Relocation — Windows'
& (Join-Path $Root 'INSTALL_AERIS_LOCAL.ps1')
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { $Python = 'python' }
& $Python -m aeris_runtime company status
if ($LASTEXITCODE -ne 0) { throw 'Company manifest validation failed.' }
& $Python -m aeris_runtime mode set $Mode
Write-Host "Runtime mode: $Mode"
& $Python -m aeris_runtime doctor
if ($LASTEXITCODE -ne 0) { Write-Warning 'Doctor is not READY. This is expected on a clean machine until local model/inference prerequisites are installed.' }
Write-Host 'Relocation bootstrap complete. Add local model assets/credentials privately, then rerun doctor.'
