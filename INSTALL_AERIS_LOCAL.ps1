param([switch]$SkipCoreSync)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root 'scripts/bootstrap.ps1') -SkipCoreSync:$SkipCoreSync
exit $LASTEXITCODE
