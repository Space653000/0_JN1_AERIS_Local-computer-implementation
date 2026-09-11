[CmdletBinding()]
param(
  [ValidateRange(0, 100000)]
  [int]$MaxTurns = 0,
  [switch]$ResetState
)

$ErrorActionPreference = 'Stop'
$Root = 'C:\0_JN1_AERIS'
$AutoRoot = Join-Path $Root '.aeris\autopilot'
$MasterTask = Join-Path $AutoRoot 'MASTER_TASK.md'
$StatePath = Join-Path $AutoRoot 'STATE.json'
$LastResult = Join-Path $AutoRoot 'LAST_RESULT.txt'
$LockPath = Join-Path $AutoRoot 'RUNNING.lock'
$ProgressUrl = 'http://127.0.0.1:8765/api/v1/progress'

function Get-ProgressSnapshot {
  try {
    $progress = Invoke-RestMethod -Uri $ProgressUrl -TimeoutSec 15
    $passCount = @($progress.items | Where-Object { $_.state -eq 'PASS' }).Count
    $evidenceCount = @($progress.items | Where-Object { $_.evidence }).Count
    $blockerCount = @($progress.items | Where-Object { $_.state -eq 'BLOCKED' }).Count
    return [ordered]@{
      available = $true
      overall = [int]$progress.overall_percent
      phases = $progress.phase_percent
      pass_count = $passCount
      evidence_count = $evidenceCount
      blocker_count = $blockerCount
      implementation_sha = $progress.implementation_sha
      captured_at_utc = [DateTime]::UtcNow.ToString('o')
    }
  } catch {
    return [ordered]@{ available = $false; error = $_.Exception.Message; captured_at_utc = [DateTime]::UtcNow.ToString('o') }
  }
}

function Test-Complete($State, $Snapshot) {
  if (-not $State.AERIS_COMPLETE -or -not $Snapshot.available) { return $false }
  foreach ($phase in 'P0','P1','P2','P3','P4','P5','P6') {
    if ([int]$Snapshot.phases.$phase -ne 100) { return $false }
  }
  return $true
}

function Test-Progress($Before, $After) {
  if (-not $Before.available -or -not $After.available) { return $false }
  return ([int]$After.overall -gt [int]$Before.overall) -or
         ([int]$After.pass_count -gt [int]$Before.pass_count) -or
         ([int]$After.evidence_count -gt [int]$Before.evidence_count) -or
         ([int]$After.blocker_count -lt [int]$Before.blocker_count)
}

if (-not (Test-Path -LiteralPath $Root)) { throw "AERIS root not found: $Root" }
foreach ($path in $AutoRoot, $MasterTask, $StatePath, $LastResult) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Required autopilot asset missing: $path" }
}

if ($ResetState) {
  [ordered]@{
    schema_version = 1; AERIS_COMPLETE = $false; turn = 0; no_progress_rounds = 0
    last_snapshot = $null; last_result = $null; stop_reason = $null; updated_at_utc = $null
  } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StatePath -Encoding utf8
  'Autopilot state reset.' | Set-Content -LiteralPath $LastResult -Encoding utf8
  exit 0
}

try {
  New-Item -ItemType File -Path $LockPath -ErrorAction Stop | Out-Null
} catch {
  throw "Autopilot already running or requires safe stale-lock review: $LockPath"
}

Set-Location $Root
$turnsRun = 0
while ($true) {
  $state = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
  $before = Get-ProgressSnapshot
  if (Test-Complete $state $before) { break }
  if ($MaxTurns -gt 0 -and $turnsRun -ge $MaxTurns) { break }

  $state.turn = [int]$state.turn + 1
  $state.stop_reason = $null
  $state.updated_at_utc = [DateTime]::UtcNow.ToString('o')
  $state.last_snapshot = $before
  $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StatePath -Encoding utf8

  $prompt = Get-Content -LiteralPath $MasterTask -Raw
  $prompt += "`n`nAUTOPILOT TURN: $($state.turn)`nPRE-TURN SNAPSHOT:`n" + ($before | ConvertTo-Json -Depth 8)
  # This installed CLI accepts global execution flags before the `exec` subcommand.
  $prompt | & codex -C $Root -m 'gpt-5.6-terra' -s danger-full-access -a never exec --output-last-message $LastResult -
  $exitCode = $LASTEXITCODE
  $after = Get-ProgressSnapshot
  $result = if (Test-Path -LiteralPath $LastResult) { Get-Content -LiteralPath $LastResult -Raw } else { '' }

  $madeProgress = Test-Progress $before $after
  $state.last_snapshot = $after
  $state.last_result = [ordered]@{ exit_code = $exitCode; made_progress = $madeProgress; captured_at_utc = [DateTime]::UtcNow.ToString('o') }
  if ($madeProgress) { $state.no_progress_rounds = 0 } else { $state.no_progress_rounds = [int]$state.no_progress_rounds + 1 }

  if ($result -match 'HUMAN_GATE_REQUIRED') { $state.stop_reason = 'HUMAN_GATE_REQUIRED' }
  elseif ($result -match 'authentication|login required|usage limit|rate limit') { $state.stop_reason = 'CODEX_AUTH_OR_USAGE_LIMIT' }
  elseif ($exitCode -ne 0) { $state.stop_reason = "CODEX_EXIT_$exitCode" }
  elseif ([int]$state.no_progress_rounds -ge 3) { $state.stop_reason = 'STOP_NO_PROGRESS' }
  $state.updated_at_utc = [DateTime]::UtcNow.ToString('o')
  $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StatePath -Encoding utf8

  $turnsRun++
  if ($state.stop_reason) { break }
}

Remove-Item -LiteralPath $LockPath -Force -ErrorAction SilentlyContinue
