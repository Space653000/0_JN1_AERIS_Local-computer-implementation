$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Core = Join-Path $Root '.aeris/core-reference'
$State = Join-Path $Root '.aeris/state/core-target.json'
$Url = 'https://github.com/Space653000/0_JN1_AERIS.git'

New-Item -ItemType Directory -Force -Path (Split-Path $Core -Parent),(Split-Path $State -Parent) | Out-Null

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git is required for core sync.' }

if (-not (Test-Path (Join-Path $Core '.git'))) {
  git clone --no-tags --filter=blob:none --branch main $Url $Core
} else {
  git -C $Core fetch --prune origin main
}

git -C $Core checkout --detach origin/main
# Local mechanism-level write guard against the canonical core repository.
git -C $Core remote set-url --push origin 'DISABLED://AERIS-CORE-READ-ONLY'
$Hook = Join-Path $Core '.git/hooks/pre-push'
@'
#!/bin/sh
echo "DENIED: AERIS canonical core repository is read-only for Codex/local implementation." >&2
exit 1
'@ | Set-Content -Path $Hook -Encoding ascii

$Sha = (git -C $Core rev-parse origin/main).Trim()
$Payload = [ordered]@{
  repository = 'Space653000/0_JN1_AERIS'
  branch = 'main'
  sha = $Sha
  synced_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  remote_write = 'DENIED'
}
$Payload | ConvertTo-Json | Set-Content -Path $State -Encoding utf8
Write-Host "Core reference synchronized read-only: $Sha" -ForegroundColor Green
