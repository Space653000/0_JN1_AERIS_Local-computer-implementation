$ErrorActionPreference='Stop'
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
. (Join-Path $Root 'scripts\windows-zero-cost-bootstrap.ps1')

$Temp=Join-Path $env:RUNNER_TEMP ("aeris-winget-zero-cost-" + [guid]::NewGuid().ToString('N'))
if(-not $env:RUNNER_TEMP){ $Temp=Join-Path $env:TEMP ("aeris-winget-zero-cost-" + [guid]::NewGuid().ToString('N')) }
New-Item -ItemType Directory -Force -Path $Temp | Out-Null
$Log=Join-Path $Temp 'args.txt'
$Shim=Join-Path $Temp 'winget.cmd'
$OldPath=$env:PATH
$OldLog=$env:AERIS_WINGET_TEST_LOG
$OldExit=$env:AERIS_WINGET_TEST_EXIT
try {
  @'
@echo off
echo %*>"%AERIS_WINGET_TEST_LOG%"
exit /b %AERIS_WINGET_TEST_EXIT%
'@ | Set-Content -Path $Shim -Encoding ascii
  $env:PATH="$Temp;$OldPath"
  $env:AERIS_WINGET_TEST_LOG=$Log
  $env:AERIS_WINGET_TEST_EXIT='0'

  $ok=Install-WingetPackageNoAgreement 'AERIS.Test.Package' 'AERIS Test Package'
  if(-not $ok){ throw 'Expected fake winget installation to return true.' }
  $args=(Get-Content $Log -Raw).Trim()
  foreach($forbidden in @('--accept-package-agreements','--accept-source-agreements')){
    if($args -match [regex]::Escape($forbidden)){ throw "Forbidden automatic agreement argument observed: $forbidden" }
  }
  foreach($required in @('install','--id','AERIS.Test.Package','-e','--source','winget','--disable-interactivity')){
    if($args -notmatch [regex]::Escape($required)){ throw "Required fail-closed winget argument missing: $required args=$args" }
  }

  $env:AERIS_WINGET_TEST_EXIT='17'
  $blocked=$false
  try {
    Install-WingetPackageNoAgreement 'AERIS.Test.Package' 'AERIS Test Package' | Out-Null
  } catch {
    if($_.Exception.Message -match 'HUMAN_GATE_PACKAGE_OR_SOURCE_AGREEMENT_OR_INSTALL_POLICY'){
      $blocked=$true
    } else { throw }
  }
  if(-not $blocked){ throw 'Expected nonzero winget exit to fail closed at the Human Gate.' }

  Write-Host 'WINDOWS_ZERO_COST_BOOTSTRAP_REGRESSION=PASS'
} finally {
  $env:PATH=$OldPath
  $env:AERIS_WINGET_TEST_LOG=$OldLog
  $env:AERIS_WINGET_TEST_EXIT=$OldExit
  Remove-Item $Temp -Recurse -Force -ErrorAction SilentlyContinue
}

# The negative-path native process intentionally exits nonzero. PowerShell preserves
# that value even though the Human-Gate exception was correctly caught and asserted.
$global:LASTEXITCODE=0
exit 0
