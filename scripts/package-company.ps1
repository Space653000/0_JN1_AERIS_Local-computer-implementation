param([string]$OutputDir = "dist")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Stage = Join-Path $Root ".aeris\package-$Stamp"
$Out = Join-Path $Root $OutputDir
New-Item -ItemType Directory -Force -Path $Stage,$Out | Out-Null
$ExcludeDirs = @('.git','.venv','.aeris','data','logs','dist','__pycache__','.pytest_cache')
Get-ChildItem -Force $Root | Where-Object { $ExcludeDirs -notcontains $_.Name -and $_.Name -ne '.env' } | ForEach-Object { Copy-Item $_.FullName -Destination $Stage -Recurse -Force }
$meta = [ordered]@{company='AERIS';image_type='portable_company_image';created_at=(Get-Date).ToUniversalTime().ToString('o');source_commit='UNKNOWN'}
try { $meta.source_commit = (git -C $Root rev-parse HEAD 2>$null).Trim() } catch {}
$meta | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Stage 'RELOCATION_MANIFEST.json')
$Zip = Join-Path $Out "AERIS-Portable-Company-$Stamp.zip"
Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $Zip -Force
Remove-Item $Stage -Recurse -Force
Write-Host "Created: $Zip"
Write-Host "Note: model weights/licenses are included only if staged as tracked/portable assets. Run doctor after relocation."
