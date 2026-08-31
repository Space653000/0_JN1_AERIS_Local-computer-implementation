param(
  [ValidateSet('auto','offline','local','cloud')][string]$Mode='auto',
  [string]$LocalModel='qwen3:4b-instruct',
  [switch]$SkipLocalModelInstall,
  [switch]$SkipCoreSync
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root 'scripts\one-click-install.ps1') -Mode $Mode -LocalModel $LocalModel -SkipLocalModelInstall:$SkipLocalModelInstall -SkipCoreSync:$SkipCoreSync
exit $LASTEXITCODE
