param(
  [ValidateSet('auto','offline','local','cloud')][string]$Mode = 'auto',
  [string]$LocalModel = 'qwen3:4b-instruct',
  [switch]$SkipLocalModelInstall,
  [switch]$SkipCoreSync
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'windows-python-resolution.ps1')
Write-Host '=== AERIS One-Click Company Installer ==='
Write-Host 'Default profile: zero paid professional software; no Claude/Claude token required.'
Write-Host 'Privacy: AERIS private engineering is application-routed to local AI; OS/network isolation still requires local verification.'

function Have($cmd){ return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Verify-StagedHash($file) {
  $sidecar="$file.sha256"
  if (-not (Test-Path $sidecar)) { throw "Staged installer requires SHA-256 sidecar: $sidecar" }
  $expected=((Get-Content $sidecar -Raw).Trim().Split()[0]).ToLowerInvariant()
  $actual=(Get-FileHash -Algorithm SHA256 $file).Hash.ToLowerInvariant()
  if ($actual -ne $expected) { throw "SHA-256 mismatch for staged installer: $file" }
}
function Install-WingetPackageNoAgreement($Id,$Label) {
  if(-not (Have 'winget')){ return $false }
  Write-Host "Installing $Label via winget without automatic agreement acceptance..."
  & winget install --id $Id -e --source winget --disable-interactivity
  if($LASTEXITCODE -ne 0){
    throw "HUMAN_GATE_PACKAGE_OR_SOURCE_AGREEMENT_OR_INSTALL_POLICY: $Label could not be installed non-interactively without AERIS accepting agreements on your behalf. Review/accept any required upstream terms manually, then rerun."
  }
  return $true
}
function Refresh-KnownToolPaths {
  foreach($candidate in @(
    "$env:LOCALAPPDATA\Programs\Ollama",
    "$env:LOCALAPPDATA\Programs\Git\cmd",
    "$env:ProgramFiles\Git\cmd"
  )){
    if((Test-Path $candidate) -and (($env:PATH -split ';') -notcontains $candidate)){
      $env:PATH += ';' + $candidate
    }
  }
}
function Set-DotEnvValue($Path,$Key,$Value) {
  $lines=@()
  if(Test-Path $Path){ $lines=@(Get-Content $Path) }
  $matched=$false
  $out=New-Object System.Collections.Generic.List[string]
  foreach($line in $lines){
    if($line -match ('^'+[regex]::Escape($Key)+'=')){
      if(-not $matched){ $out.Add("$Key=$Value") }
      $matched=$true
    } else {
      $out.Add([string]$line)
    }
  }
  if(-not $matched){ $out.Add("$Key=$Value") }
  $out | Set-Content -Path $Path -Encoding utf8
}
function Test-OllamaModel($Model) {
  if(-not (Have 'ollama')){ return $false }
  & ollama show $Model *> $null
  return ($LASTEXITCODE -eq 0)
}
function Install-StagedModel($Model) {
  $ModelsRoot=Join-Path $Root 'portable_assets\models'
  $ManifestPath=Join-Path $ModelsRoot 'model.manifest.json'
  if(-not (Test-Path $ManifestPath)){ return $false }
  $m=Get-Content $ManifestPath -Raw | ConvertFrom-Json
  if($m.schema_version -ne 1){ throw 'Unsupported staged model manifest schema.' }
  if($m.model_name -ne $Model){ throw "Staged model manifest targets '$($m.model_name)' but installer requested '$Model'." }
  if($m.format -ne 'gguf'){ throw "Unsupported staged model format '$($m.format)'. Current offline importer supports gguf." }
  $ModelFile=Join-Path $ModelsRoot $m.file
  if(-not (Test-Path $ModelFile)){ throw "Staged model file missing: $ModelFile" }
  $actual=(Get-FileHash -Algorithm SHA256 $ModelFile).Hash.ToLowerInvariant()
  if($actual -ne ([string]$m.sha256).ToLowerInvariant()){ throw 'Staged model SHA-256 does not match model.manifest.json.' }
  $Modelfile=Join-Path $Root '.aeris\installers\Modelfile.offline'
  $portablePath=$ModelFile.Replace('\','/')
  "FROM `"$portablePath`"" | Set-Content -Path $Modelfile -Encoding ascii
  Write-Host "Importing checksum-verified staged GGUF model as $Model..."
  & ollama create $Model -f $Modelfile
  if($LASTEXITCODE -ne 0){ throw 'Ollama staged model import failed.' }
  return $true
}

$PythonExe=Resolve-AerisPython
if (-not $PythonExe) {
  $StagedPython=Join-Path $Root 'portable_assets\installers\python-3.11-amd64.exe'
  if(Test-Path $StagedPython){
    Verify-StagedHash $StagedPython
    Write-Host 'Installing checksum-verified staged Python 3.11...'
    Start-Process -FilePath $StagedPython -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1' -Wait
    $PythonExe=Resolve-AerisPython
  } elseif($Mode -eq 'offline') {
    throw 'Offline clean-machine install requires portable_assets/installers/python-3.11-amd64.exe plus .sha256, or preinstalled Python 3.10+.'
  } elseif (Install-WingetPackageNoAgreement 'Python.Python.3.11' 'Python 3.11') {
    $PythonExe=Resolve-AerisPython
  }
  if (-not $PythonExe) { throw 'Python 3.10+ could not be installed automatically without bypassing AERIS license/agreement policy. See docs/ONE_CLICK_INSTALL.md.' }
}
$PythonExe=Assert-AerisPythonVersion -Executable $PythonExe
Write-Host "Python interpreter: $PythonExe"

Push-Location $Root
try {
  if (-not (Test-Path '.venv')) { & $PythonExe -m venv .venv }
  if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
  $Py=Join-Path $Root '.venv\Scripts\python.exe'
  if (-not (Test-Path $Py -PathType Leaf)) { throw "AERIS virtualenv interpreter missing after creation: $Py" }
  if (-not (Test-Path '.env') -and (Test-Path '.env.example')) { Copy-Item '.env.example' '.env' }
  Set-DotEnvValue '.env' 'AERIS_LOCAL_MODEL' $LocalModel
  New-Item -ItemType Directory -Force -Path '.aeris\state','.aeris\knowledge','.aeris\ingress','.aeris\installers','data','logs' | Out-Null

  if (-not $SkipCoreSync -and -not (Have 'git') -and $Mode -ne 'offline') {
    if(Install-WingetPackageNoAgreement 'Git.Git' 'Git'){
      Refresh-KnownToolPaths
    }
    if(-not (Have 'git')){
      throw 'Git is required for clean online canonical Core synchronization and could not be installed under the zero-cost/no-auto-agreement policy.'
    }
  }

  if (-not $SkipCoreSync) {
    $StagedCore=Join-Path $Root 'portable_assets\core-reference'
    if ((Test-Path $StagedCore) -and -not (Test-Path '.aeris\core-reference')) {
      Write-Host 'Restoring staged read-only Core reference...'
      Copy-Item $StagedCore '.aeris\core-reference' -Recurse -Force
    } elseif (Have 'git') {
      try { & (Join-Path $PSScriptRoot 'sync-core.ps1') } catch { Write-Warning "Core sync failed; cached/staged Core will be used if present: $($_.Exception.Message)" }
    }
    if(-not (Test-Path '.aeris\core-reference')){
      if($Mode -eq 'offline'){ throw 'Offline install requires portable_assets/core-reference or an existing verified Core cache.' }
      Write-Warning 'Canonical Core cache is absent; local acceptance will remain BLOCKED until Core is synchronized.'
    }
  }

  if (-not $SkipLocalModelInstall -and -not (Have 'ollama')) {
    $Staged=Join-Path $Root 'portable_assets\installers\OllamaSetup.exe'
    if (Test-Path $Staged) {
      Verify-StagedHash $Staged
      Write-Host 'Installing checksum-verified staged Ollama package...'
      Start-Process -FilePath $Staged -ArgumentList '/S' -Wait
    } elseif ($Mode -eq 'offline') {
      throw 'Offline install requires a checksum-verified portable_assets/installers/OllamaSetup.exe or preinstalled Ollama.'
    } elseif (Install-WingetPackageNoAgreement 'Ollama.Ollama' 'Ollama') {
      Refresh-KnownToolPaths
    } else { throw 'Ollama could not be installed automatically under the zero-cost/no-auto-agreement policy. Stage a verified installer or install it before rerunning.' }
    Refresh-KnownToolPaths
  }

  if (-not $SkipLocalModelInstall -and (Have 'ollama')) {
    try { ollama list | Out-Null } catch {
      Write-Host 'Starting local Ollama service...'
      Start-Process -FilePath (Get-Command ollama).Source -ArgumentList 'serve' -WindowStyle Hidden
      Start-Sleep -Seconds 4
    }
    if(-not (Test-OllamaModel $LocalModel)){
      $Imported=Install-StagedModel $LocalModel
      if(-not $Imported){
        if($Mode -eq 'offline'){ throw "Offline mode requires staged model assets for '$LocalModel' or a preinstalled model." }
        Write-Host "Pulling local model: $LocalModel"
        & ollama pull $LocalModel
        if($LASTEXITCODE -ne 0){ throw 'Ollama model pull failed.' }
      }
    }
  }

  & $Py -c "from aeris_runtime.deployment_policy import validate_default_deployment; r=validate_default_deployment(); print('ZERO_COST_NO_CLAUDE_POLICY=' + ('PASS' if r['valid'] else 'FAIL')); raise SystemExit(0 if r['valid'] else 19)"
  if($LASTEXITCODE -ne 0){ throw 'AERIS zero-cost/no-Claude deployment policy validation failed.' }
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
  Write-Host 'AERIS bootstrap finished. INSTALLATION IS NOT THE SAME AS VERIFIED.' -ForegroundColor Green
  Write-Host 'Private engineering: python -m aeris_runtime chat "..."  (LOCAL ONLY)'
  Write-Host 'Public research:     python -m aeris_runtime research "..." (PUBLIC QUERY ONLY)'
  Write-Host 'Knowledge search:    python -m aeris_runtime knowledge search "beamforming"'
  Write-Host 'Next: run scripts\local-acceptance.ps1 before declaring this machine VERIFIED.'
} finally { Pop-Location }
