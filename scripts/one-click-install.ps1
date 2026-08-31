param(
  [ValidateSet('auto','offline','local','cloud')][string]$Mode = 'auto',
  [string]$LocalModel = 'qwen3:4b-instruct',
  [switch]$SkipLocalModelInstall,
  [switch]$SkipCoreSync
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Write-Host '=== AERIS One-Click Company Installer ==='
Write-Host 'Privacy: local/private data never auto-egresses to public cloud.'

function Have($cmd){ return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Resolve-Python {
  $p=Get-Command python -ErrorAction SilentlyContinue
  if ($p) { return $p.Source }
  $candidates=@(
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:ProgramFiles\Python311\python.exe"
  )
  foreach($c in $candidates){ if(Test-Path $c){ return $c } }
  $found=Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if($found){ return $found.FullName }
  return $null
}
function Assert-PythonVersion($exe) {
  $ok=& $exe -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 9)"
  if ($LASTEXITCODE -ne 0) { throw 'AERIS requires Python 3.10 or newer.' }
}
function Verify-StagedHash($file) {
  $sidecar="$file.sha256"
  if (-not (Test-Path $sidecar)) { throw "Staged installer requires SHA-256 sidecar: $sidecar" }
  $expected=((Get-Content $sidecar -Raw).Trim().Split()[0]).ToLowerInvariant()
  $actual=(Get-FileHash -Algorithm SHA256 $file).Hash.ToLowerInvariant()
  if ($actual -ne $expected) { throw "SHA-256 mismatch for staged installer: $file" }
}

$PythonExe=Resolve-Python
if ($PythonExe) {
  try { Assert-PythonVersion $PythonExe } catch { $PythonExe=$null }
}
if (-not $PythonExe) {
  if (Have 'winget') {
    Write-Host 'Installing Python 3.11 via winget...'
    winget install --id Python.Python.3.11 -e --accept-package-agreements --accept-source-agreements
    $PythonExe=Resolve-Python
  }
  if (-not $PythonExe) { throw 'Python 3.10+ could not be installed automatically. See docs/ONE_CLICK_INSTALL.md.' }
  Assert-PythonVersion $PythonExe
}

Push-Location $Root
try {
  if (-not (Test-Path '.venv')) { & $PythonExe -m venv .venv }
  $Py=Join-Path $Root '.venv\Scripts\python.exe'
  if (-not (Test-Path '.env') -and (Test-Path '.env.example')) { Copy-Item '.env.example' '.env' }
  New-Item -ItemType Directory -Force -Path '.aeris\state','.aeris\knowledge','.aeris\ingress','.aeris\installers','data','logs' | Out-Null

  if (-not $SkipCoreSync) {
    $StagedCore=Join-Path $Root 'portable_assets\core-reference'
    if ((Test-Path $StagedCore) -and -not (Test-Path '.aeris\core-reference')) {
      Write-Host 'Restoring staged read-only Core reference...'
      Copy-Item $StagedCore '.aeris\core-reference' -Recurse -Force
    } elseif (Have 'git') {
      try { & (Join-Path $PSScriptRoot 'sync-core.ps1') } catch { Write-Warning "Core sync failed; cached/staged Core will be used if present: $($_.Exception.Message)" }
    } else {
      Write-Warning 'Git unavailable; Core cannot be refreshed. Offline install requires portable_assets/core-reference.'
    }
  }

  if (-not $SkipLocalModelInstall -and -not (Have 'ollama')) {
    $Staged=Join-Path $Root 'portable_assets\installers\OllamaSetup.exe'
    if (Test-Path $Staged) {
      Verify-StagedHash $Staged
      Write-Host 'Installing checksum-verified staged Ollama package...'
      Start-Process -FilePath $Staged -ArgumentList '/S' -Wait
    } elseif (Have 'winget') {
      Write-Host 'Installing Ollama via winget...'
      winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
    } else { throw 'Ollama could not be installed automatically. Stage a verified installer or install it before rerunning.' }
    $env:PATH += ';' + "$env:LOCALAPPDATA\Programs\Ollama"
  }

  if (-not $SkipLocalModelInstall -and (Have 'ollama')) {
    try { ollama list | Out-Null } catch {
      Write-Host 'Starting local Ollama service...'
      Start-Process -FilePath (Get-Command ollama).Source -ArgumentList 'serve' -WindowStyle Hidden
      Start-Sleep -Seconds 4
    }
    Write-Host "Ensuring local model: $LocalModel"
    ollama pull $LocalModel
  }

  & $Py -m aeris_runtime mode set $Mode
  & $Py -m aeris_runtime machine detect --write
  & $Py -m aeris_runtime knowledge build
  & $Py -m unittest discover -s tests -v
  if ($LASTEXITCODE -ne 0) { throw 'AERIS unit tests failed.' }
  & $Py -m aeris_runtime company status
  if ($LASTEXITCODE -ne 0) { throw 'AERIS company manifest validation failed.' }
  & $Py -m aeris_runtime doctor
  $doctor=$LASTEXITCODE
  if (-not $SkipLocalModelInstall -and $doctor -ne 0) { throw "AERIS local continuity verification failed (doctor exit $doctor)." }
  if ($doctor -ne 0) { Write-Warning "AERIS installed with limits because local-model installation was explicitly skipped (doctor exit $doctor)." }
  Write-Host ''
  Write-Host 'AERIS bootstrap finished.' -ForegroundColor Green
  Write-Host 'Private engineering: python -m aeris_runtime chat "..."  (LOCAL ONLY)'
  Write-Host 'Public research:     python -m aeris_runtime research "..." (PUBLIC QUERY ONLY)'
  Write-Host 'Knowledge search:    python -m aeris_runtime knowledge search "beamforming"'
  Write-Host 'Next: run scripts\local-acceptance.ps1 before declaring this machine VERIFIED.'
} finally { Pop-Location }
