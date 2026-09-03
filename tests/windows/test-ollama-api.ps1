$ErrorActionPreference='Stop'
$Root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $Root 'scripts\windows-ollama-api.ps1')
$script:Requests=@()
function Invoke-RestMethod {
  param($Uri,$Method,$TimeoutSec,$ContentType,$Body)
  $script:Requests += @{Uri=$Uri;Method=$Method;Body=$Body;Timeout=$TimeoutSec}
  if($script:Unavailable){ throw 'offline' }
  if($Uri -like '*/api/tags'){ return [pscustomobject]@{models=@()} }
  return [pscustomobject]@{details=@{family='qwen3'}}
}
function ollama { throw 'CLI must not be invoked by API probes' }
$script:Unavailable=$false
if(-not (Test-AerisOllamaApi 'http://127.0.0.1:11434')){ throw 'API presence rejected' }
if(-not (Test-AerisOllamaModel 'http://127.0.0.1:11434' 'qwen3:4b-instruct')){ throw 'Installed model rejected' }
if(($script:Requests[-1].Body | ConvertFrom-Json).model -ne 'qwen3:4b-instruct'){ throw 'Model request lost exact identity' }
$script:Unavailable=$true
if(Test-AerisOllamaApi 'http://127.0.0.1:11434'){ throw 'Unavailable API was accepted' }
if(Test-AerisOllamaModel 'http://127.0.0.1:11434' 'missing'){ throw 'Missing model was accepted' }
$old=$env:AERIS_LOCAL_BASE_URL
try {
  $env:AERIS_LOCAL_BASE_URL='https://example.com'
  $rejected=$false
  try { Get-AerisOllamaBaseUrl $Root | Out-Null } catch { $rejected=$true }
  if(-not $rejected){ throw 'External endpoint was accepted' }
} finally { $env:AERIS_LOCAL_BASE_URL=$old }
'WINDOWS_OLLAMA_API_REGRESSION=PASS'
