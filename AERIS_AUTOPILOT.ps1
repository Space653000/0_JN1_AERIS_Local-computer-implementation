param(
  [ValidateSet('auto','offline','local','cloud')][string]$Mode='auto',
  [string]$LocalModel='qwen3:4b-instruct',
  [switch]$HardOffline,
  [switch]$CISmoke,
  [switch]$NoSupervisor
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root 'scripts\autopilot.ps1') -Mode $Mode -LocalModel $LocalModel -HardOffline:$HardOffline -CISmoke:$CISmoke -NoSupervisor:$NoSupervisor
exit $LASTEXITCODE
