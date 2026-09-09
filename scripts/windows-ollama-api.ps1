# Probe the running API without invoking the Windows CLI's desktop-app autostart.
function Get-AerisOllamaBaseUrl {
  param([string]$Root)
  $value=$env:AERIS_LOCAL_BASE_URL
  if(-not $value -and (Test-Path (Join-Path $Root '.env'))){
    $line=Get-Content (Join-Path $Root '.env') | Where-Object { $_ -match '^AERIS_LOCAL_BASE_URL=' } | Select-Object -Last 1
    if($line){ $value=$line.Substring('AERIS_LOCAL_BASE_URL='.Length).Trim() }
  }
  if(-not $value){ $value='http://127.0.0.1:11434' }
  $uri=[uri]$value
  if($uri.Scheme -ne 'http' -or $uri.Host -notin @('127.0.0.1','localhost','[::1]','::1') -or $uri.UserInfo -or $uri.Query -or $uri.Fragment){
    throw 'AERIS installer requires an unauthenticated loopback Ollama HTTP endpoint.'
  }
  return $value.TrimEnd('/')
}

function Test-AerisOllamaApi {
  param([string]$BaseUrl)
  try {
    $response=Invoke-RestMethod -Uri "$BaseUrl/api/tags" -Method Get -TimeoutSec 5
    return ($null -ne $response -and $response.PSObject.Properties.Name -contains 'models')
  } catch { return $false }
}

function Test-AerisOllamaModel {
  param([string]$BaseUrl,[string]$Model)
  try {
    $response=Invoke-RestMethod -Uri "$BaseUrl/api/show" -Method Post -ContentType 'application/json' -Body (@{model=$Model} | ConvertTo-Json -Compress) -TimeoutSec 10
    return ($null -ne $response -and $response.PSObject.Properties.Name -contains 'details')
  } catch { return $false }
}
