param([switch]$CISmoke)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root 'scripts\claude-verify.ps1') -CISmoke:$CISmoke
exit $LASTEXITCODE
