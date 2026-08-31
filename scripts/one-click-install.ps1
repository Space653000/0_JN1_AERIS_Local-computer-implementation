param(
  [ValidateSet('auto','offline','local','cloud')][string]$Mode = 'auto',
  [string]$LocalModel = 'qwen2.5:3b',
  [switch]$SkipLocalModelInstall
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Write-Host '=== AERIS One-Click Company Installer ==='
Write-Host 'Policy: local data stays local; cloud is public-information ingress only.'

function Have($cmd){ return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
if (-not (Have 'python')) {
  if (Have 'winget') {
    Write-Host 'Installing Python 3.11 via winget...'
    winget install --id Python.Python.3.11 -e --accept-package-agreements --accept-source-agreements
  } else { throw 'Python 3.10+ is required. Install Python, then rerun this installer.' }
}
Push-Location $Root
try {
  if (-not (Test-Path '.venv')) { python -m venv .venv }
  $Py=Join-Path $Root '.venv\Scripts\python.exe'
  if (-not (Test-Path '.env') -and (Test-Path '.env.example')) { Copy-Item '.env.example' '.env' }
  New-Item -ItemType Directory -Force -Path '.aeris\state','.aeris\knowledge','.aeris\ingress','data','logs' | Out-Null
  if (-not $SkipLocalModelInstall -and -not (Have 'ollama')) {
    if (Have 'winget') {
      Write-Host 'Installing Ollama via winget...'
      winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
      $env:PATH += ';' + "$env:LOCALAPPDATA\Programs\Ollama"
    } else { Write-Warning 'Ollama not found and winget unavailable. Install manually or stage portable_assets.' }
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
  Write-Host 'AERIS installation finished.'
  Write-Host 'Private engineering chat: python -m aeris_runtime chat "..."  (LOCAL ONLY)'
  Write-Host 'Public cloud research:   python -m aeris_runtime research "..." (NO LOCAL CONTEXT)'
  Write-Host 'Knowledge search:        python -m aeris_runtime knowledge search "beamforming"'
} finally { Pop-Location }
