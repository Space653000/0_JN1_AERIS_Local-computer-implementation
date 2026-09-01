function Install-WingetPackageNoAgreement {
  param(
    [Parameter(Mandatory=$true)][string]$Id,
    [Parameter(Mandatory=$true)][string]$Label
  )
  $cmd=Get-Command winget -ErrorAction SilentlyContinue
  if(-not $cmd){ return $false }
  Write-Host "Installing $Label via winget without automatic agreement acceptance..."
  & $cmd.Source install --id $Id -e --source winget --disable-interactivity
  if($LASTEXITCODE -ne 0){
    throw "HUMAN_GATE_PACKAGE_OR_SOURCE_AGREEMENT_OR_INSTALL_POLICY: $Label could not be installed non-interactively without AERIS accepting agreements on your behalf. Review/accept any required upstream terms manually, then rerun."
  }
  return $true
}

function Refresh-AerisKnownToolPaths {
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
