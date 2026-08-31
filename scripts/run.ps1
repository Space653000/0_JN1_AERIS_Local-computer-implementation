param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$RuntimeArgs
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv/Scripts/python.exe'
if (-not (Test-Path $Python)) { $Python = (Get-Command python).Source }
Set-Location $Root
& $Python -m aeris_runtime @RuntimeArgs
exit $LASTEXITCODE
