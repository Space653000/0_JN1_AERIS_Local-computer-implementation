param([ValidateSet('auto','offline','local','cloud')][string]$Mode='auto')
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root 'scripts\one-click-install.ps1') -Mode $Mode
exit $LASTEXITCODE
