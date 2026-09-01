$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $RepoRoot 'scripts\windows-python-resolution.ps1')

$realPython = (Get-Command python -ErrorAction Stop).Source
$realPython = (Resolve-Path -LiteralPath $realPython).Path
if (-not (Test-AerisPythonExecutable -Executable $realPython)) {
  throw "CI Python must be a supported executable interpreter: $realPython"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("aeris-python-resolver-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
$oldPath = $env:PATH
try {
  @'
@echo off
exit /b 9009
'@ | Set-Content -LiteralPath (Join-Path $tempRoot 'python.cmd') -Encoding ascii

  $escapedReal = $realPython.Replace('%','%%')
  @"
@echo off
if "%1"=="-3.11" exit /b 3
if "%1"=="-3" (
  if "%2"=="-c" (
    echo $escapedReal
    exit /b 0
  )
)
exit /b 4
"@ | Set-Content -LiteralPath (Join-Path $tempRoot 'py.cmd') -Encoding ascii

  $env:PATH = "$tempRoot;$oldPath"

  $storeAlias = (Get-Command python -ErrorAction Stop).Source
  if ((Test-AerisPythonExecutable -Executable $storeAlias)) {
    throw 'Broken Windows Store-style python shim must be rejected.'
  }

  $resolved = Resolve-AerisPython
  if (-not $resolved) { throw 'Resolver returned no Python while py -3 provided a supported interpreter.' }
  $resolved = (Resolve-Path -LiteralPath $resolved).Path
  if ($resolved -ne $realPython) {
    throw "Resolver should fall back from failed py -3.11 to supported py -3. Expected '$realPython', got '$resolved'."
  }

  Write-Host "WINDOWS_PYTHON_RESOLVER_REGRESSION=PASS ($resolved)"
} finally {
  $env:PATH = $oldPath
  Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
