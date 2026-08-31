param(
  [ValidateSet('auto','offline','local','cloud')][string]$Mode = 'auto',
  [string]$LocalModel = 'qwen2.5:3b',
  [switch]$SkipLocalModelInstall
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

$PythonExe=Resolve-Python
if (-not $PythonExe) {
  if (Have 'winget') {
    Write-Host 'Installing Python 3.11 via winget...'
    winget install --id Python.Python.3.11 -e --accept-package-agreements --accept-source-agreements
    $PythonExe=Resolve-Python
  }
  if (-not $PythonExe) { throw 'Python 3.10+ could not be installed automatically. See docs/ONE_CLICK_INSTALL.md.' }
}

Push-Location $Root
try {
  if (-not (Test-Path '.venv')) { & $PythonExe -m venv .venv }
  $Py=Join-Path $Root '.venv\Scripts\python.exe'
  if (-not (Test-Path '.env') -and (Test-Path '.env.example')) { Copy-Item '.env.example' '.env' }
  New-Item -ItemType Directory -Force -Path '.aeris\state','.aeris\knowledge','.aeris\ingress','.aeris\installers','data','logs' | Out-Null

  if (-not $SkipLocalModelInstall -and -not (Have 'ollama')) {
    $Staged=Join-Path $Root 'portable_assets\installers\OllamaSetup.exe'
    if (Test-Path $Staged) {
      Write-Host 'Installing staged Ollama package...'
      Start-Process -FilePath $Staged -ArgumentList '/S' -Wait
    } elseif (Have 'winget') {
      Write-Host 'Installing Ollama via winget...'
      winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
    } else { Write-Warning 'Ollama could not be installed automatically. Use portable_assets or deployment guide.' }
    $env:PATH += ';' + "$env:LOCALAPPDATA\Programs\Ollama"
  }

  if (-not $SkipLocalModelInstall -and (Have 'ollama')) {
    Write-Host "Ensuring local model: $LocalModel"
    try { ollama pull $LocalModel } catch { Write-Warning "Model pull failed. If offline, stage the model before deployment. $_" }
  }

  & $Py -m aeris_runtime mode set $Mode
  & $Py -m aeris_runtime machine detect --write
  & $Py -m aeris_runtime knowledge build
  & $Py -m unittest discover -s tests -v
  & $Py -m aeris_runtime company status
  & $Py -m aeris_runtime doctor
  Write-Host ''
  Write-Host 'AERIS bootstrap finished.'
  Write-Host 'Private engineering: python -m aeris_runtime chat "..."  (LOCAL ONLY)'
  Write-Host 'Public research:     python -m aeris_runtime research "..." (NO LOCAL CONTEXT)'
  Write-Host 'Knowledge search:    python -m aeris_runtime knowledge search "beamforming"'
} finally { Pop-Location }
