param([string]$OutputDir = "dist")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Stage = Join-Path $Root ".aeris\package-$Stamp"
$Out = Join-Path $Root $OutputDir
New-Item -ItemType Directory -Force -Path $Stage,$Out | Out-Null
$ExcludeDirs = @('.git','.venv','.aeris','data','logs','dist','dist-ci','portable_assets','private-backups','__pycache__','.pytest_cache')
Get-ChildItem -Force $Root | Where-Object { $ExcludeDirs -notcontains $_.Name -and $_.Name -ne '.env' } | ForEach-Object { Copy-Item $_.FullName -Destination $Stage -Recurse -Force }
$meta = [ordered]@{
  company='AERIS'
  image_type='portable_company_image'
  image_scope='SOFTWARE_ONLY_NO_PRIVATE_STATE_NO_PRIVATE_ASSETS'
  created_at=(Get-Date).ToUniversalTime().ToString('o')
  source_commit='UNKNOWN'
  private_state_included=$false
  portable_assets_included=$false
  release_metadata='release-metadata/'
  restore_requirement='For full relocation, separately supply encrypted private state and Human-controlled Private Asset Pack, then run local acceptance.'
}
try { $meta.source_commit = (git -C $Root rev-parse HEAD 2>$null).Trim() } catch {}
$meta | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Stage 'RELOCATION_MANIFEST.json')
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if(-not (Test-Path $Python)){
  $cmd=Get-Command python -ErrorAction SilentlyContinue
  if($cmd){ $Python=$cmd.Source } else { throw 'Python is required to generate SBOM/provenance metadata before packaging.' }
}
& $Python (Join-Path $Stage 'scripts\release-metadata.py') --root $Stage --output (Join-Path $Stage 'release-metadata') --source-commit $meta.source_commit
if($LASTEXITCODE -ne 0){ throw 'Release metadata generation failed.' }
$Zip = Join-Path $Out "AERIS-Portable-Company-Software-$Stamp.zip"
Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $Zip -Force
Remove-Item $Stage -Recurse -Force
$Hash = (Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLowerInvariant()
$Sidecar = "$Zip.sha256"
"$Hash  $([IO.Path]::GetFileName($Zip))" | Set-Content -Encoding ascii $Sidecar
Write-Host "Created software-only package: $Zip"
Write-Host "Created external package digest: $Sidecar"
Write-Host 'Package includes SBOM.spdx.json, PROVENANCE.json and SHA256SUMS under release-metadata/.'
Write-Host 'The SHA-256 sidecar provides transfer integrity only; production authenticity still requires a trusted signing/attestation policy.'
Write-Host 'Private state and portable_assets were deliberately excluded. See docs/deployment/STATE_BACKUP_RESTORE.md.'
