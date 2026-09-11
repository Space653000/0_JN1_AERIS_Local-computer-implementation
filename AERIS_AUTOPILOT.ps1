[CmdletBinding()]
param(
  [ValidateRange(0, 100000)]
  [int]$MaxTurns = 0,
  [ValidateRange(1, 1440)]
  [int]$QuotaRetryMinutes = 15,
  [switch]$DryRun,
  [switch]$ValidateOnly,
  [switch]$ResetState
)

$ErrorActionPreference = 'Stop'
$Root = 'C:\0_JN1_AERIS'
$SupervisionRoot = 'C:\0_JN1_AERIS_PARALLEL_STAGING'
$AutoRoot = Join-Path $Root '.aeris\autopilot'
$MasterTask = Join-Path $AutoRoot 'MASTER_TASK.md'
$StatePath = Join-Path $AutoRoot 'STATE.json'
$LastResult = Join-Path $AutoRoot 'LAST_RESULT.txt'
$TurnOutput = Join-Path $AutoRoot 'TURN_OUTPUT.txt'
$LockPath = Join-Path $AutoRoot 'RUNNING.lock'
$ProgressUrl = 'http://127.0.0.1:8765/api/v1/progress'

function Write-AtomicJson($Path, $Value) {
  $temporary = "$Path.tmp"
  $Value | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $temporary -Encoding utf8
  Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function New-AutopilotState {
  [ordered]@{
    schema_version = 2; status = 'READY'; AERIS_COMPLETE = $false; turn = 0
    current_phase = $null; current_item = $null; no_progress_rounds = 0
    last_snapshot = $null; last_evidence = $null; next_action = $null
    last_result = $null; quota_retry_at_utc = $null; stop_reason = $null
    supervision_root = $SupervisionRoot; updated_at_utc = [DateTime]::UtcNow.ToString('o')
  }
}

function Read-State {
  $state = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
  foreach ($property in (New-AutopilotState).Keys) {
    if ($null -eq $state.PSObject.Properties[$property]) {
      $state | Add-Member -NotePropertyName $property -NotePropertyValue $null
    }
  }
  if ($null -eq $state.schema_version) { $state.schema_version = 2 }
  return $state
}

function Get-GitValue([string[]]$Arguments) {
  $value = & git @Arguments 2>$null
  if ($LASTEXITCODE -ne 0) { return $null }
  return ($value | Select-Object -First 1).Trim()
}

function Get-ProgressSnapshot {
  $head = Get-GitValue @('rev-parse', 'HEAD')
  $originMain = Get-GitValue @('rev-parse', 'origin/main')
  $branch = Get-GitValue @('branch', '--show-current')
  $dirty = [bool](& git status --porcelain)
  $supervisionAvailable = Test-Path -LiteralPath $SupervisionRoot
  try {
    $progress = Invoke-RestMethod -Uri $ProgressUrl -TimeoutSec 15
    $passCount = @($progress.items | Where-Object { $_.state -eq 'PASS' }).Count
    $evidenceCount = @($progress.items | Where-Object { $_.evidence }).Count
    $blockerCount = @($progress.items | Where-Object { $_.state -eq 'BLOCKED' }).Count
    $runtimeSha = [string]$progress.implementation_sha
    return [ordered]@{
      available = $true; local_head = $head; origin_main_sha = $originMain; branch = $branch; dirty = $dirty
      runtime_sha = $runtimeSha; candidate_aligned = ($head -eq $runtimeSha)
      aeris_complete = [bool]$progress.aeris_complete
      supervision_root = $SupervisionRoot; supervision_root_available = $supervisionAvailable
      overall = [int]$progress.overall_percent; phases = $progress.phase_percent
      pass_count = $passCount; evidence_count = $evidenceCount; blocker_count = $blockerCount
      captured_at_utc = [DateTime]::UtcNow.ToString('o')
    }
  } catch {
    return [ordered]@{
      available = $false; local_head = $head; origin_main_sha = $originMain; branch = $branch; dirty = $dirty
      runtime_sha = $null; candidate_aligned = $false; supervision_root = $SupervisionRoot
      aeris_complete = $false
      supervision_root_available = $supervisionAvailable; error = $_.Exception.Message
      captured_at_utc = [DateTime]::UtcNow.ToString('o')
    }
  }
}

function Test-Complete($State, $Snapshot) {
  if (-not $Snapshot.available -or -not $Snapshot.candidate_aligned -or -not $Snapshot.aeris_complete) { return $false }
  foreach ($phase in 'P0','P1','P2','P3','P4','P5','P6') {
    if ([int]$Snapshot.phases.$phase -ne 100) { return $false }
  }
  return $true
}

function Test-Progress($Before, $After) {
  if (-not $Before.available -or -not $After.available -or -not $After.candidate_aligned) { return $false }
  return ([int]$After.overall -gt [int]$Before.overall) -or
         ([int]$After.pass_count -gt [int]$Before.pass_count) -or
         ([int]$After.evidence_count -gt [int]$Before.evidence_count) -or
         ([int]$After.blocker_count -lt [int]$Before.blocker_count)
}

function Get-FieldFromResult {
  param([string]$Result, [string]$Field)
  $match = [regex]::Match($Result, "(?mi)^${Field}:\s*(.+)$")
  if ($match.Success) { return [string]$match.Groups[1].Value.Trim() }
  return $null
}

function Test-QuotaResult($Result) {
  return $Result -match '(?i)usage limit|quota(\s|_|-)exhausted|rate limit|too many requests|\b429\b'
}

function Test-HumanGateResult($Result) {
  return $Result -match '(?mi)^HUMAN_GATE_REQUIRED\b|^BLOCKED_EXTERNAL\b'
}

function Ensure-AutopilotBranch {
  $branch = Get-GitValue @('branch', '--show-current')
  if ($branch -and $branch -ne 'main') { return $branch }
  $head = Get-GitValue @('rev-parse', '--short=12', 'HEAD')
  $name = "codex/autopilot/$([DateTime]::UtcNow.ToString('yyyyMMddHHmmss'))-$head"
  & git switch -c $name
  if ($LASTEXITCODE -ne 0) { throw 'Unable to create an autopilot work branch; main will not be used.' }
  return $name
}

function Test-RunningProcess([int]$ProcessId) {
  if ($ProcessId -le 0) { return $false }
  return $null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)
}

function Recover-StaleLock {
  if (-not (Test-Path -LiteralPath $LockPath)) { return }
  $owner = $null
  try { $owner = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json } catch { }
  if ($owner -and (Test-RunningProcess ([int]$owner.process_id))) {
    throw "Autopilot already running (PID $($owner.process_id)); refusing a concurrent turn."
  }
  Remove-Item -LiteralPath $LockPath -Force
}

foreach ($path in $Root, $AutoRoot, $MasterTask, $StatePath) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Required autopilot asset missing: $path" }
}

if ($ResetState) {
  Write-AtomicJson $StatePath (New-AutopilotState)
  'Autopilot state reset.' | Set-Content -LiteralPath $LastResult -Encoding utf8
  exit 0
}

Recover-StaleLock

if ($ValidateOnly) { exit 0 }

if (-not $DryRun) { [void](Ensure-AutopilotBranch) }

[ordered]@{ process_id = $PID; started_at_utc = [DateTime]::UtcNow.ToString('o'); root = $Root } |
  ConvertTo-Json | Set-Content -LiteralPath $LockPath -Encoding utf8
try {
  Set-Location $Root
  $turnsRun = 0
  while ($true) {
    $state = Read-State
    $before = Get-ProgressSnapshot
    if (Test-Complete $state $before) {
      $state.AERIS_COMPLETE = $true; $state.status = 'COMPLETE'; $state.stop_reason = 'AERIS_COMPLETE'; $state.updated_at_utc = [DateTime]::UtcNow.ToString('o')
      Write-AtomicJson $StatePath $state
      break
    }
    if ($MaxTurns -gt 0 -and $turnsRun -ge $MaxTurns) { break }

    $state.turn = [int]$state.turn + 1
    $state.status = if ($DryRun) { 'DRY_RUN' } else { 'RUNNING' }
    $state.stop_reason = $null; $state.last_snapshot = $before
    $state.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    Write-AtomicJson $StatePath $state

    $prompt = Get-Content -LiteralPath $MasterTask -Raw
    $prompt += "`n`nAUTOPILOT TURN: $($state.turn)`nMODE: " + $(if ($DryRun) { 'DRY_RUN' } else { 'CONSTRUCTION' })
    $prompt += "`nPRE-TURN SNAPSHOT:`n" + ($before | ConvertTo-Json -Depth 20)
    if ($DryRun) {
      $prompt += "`nDRY RUN ONLY: Read the required targeted state, select the current next item, make no product or Git changes, run no broad test, and return RESULT: NO_CHANGE with the selected ITEM and NEXT."
    }

    '' | Set-Content -LiteralPath $LastResult -Encoding utf8
    $cliOutput = $prompt | & codex -C $Root -m 'gpt-5.6-terra' -s danger-full-access -a never exec --output-last-message $LastResult - 2>&1 | Out-String
    $cliOutput | Set-Content -LiteralPath $TurnOutput -Encoding utf8
    $exitCode = $LASTEXITCODE
    $after = Get-ProgressSnapshot
    $result = if (Test-Path -LiteralPath $LastResult) { Get-Content -LiteralPath $LastResult -Raw } else { '' }
    $item = Get-FieldFromResult -Result $result -Field 'ITEM'
    $evidence = Get-FieldFromResult -Result $result -Field 'EVIDENCE'
    $next = Get-FieldFromResult -Result $result -Field 'NEXT'
    $madeProgress = Test-Progress $before $after
    $meaningfulTurn = $madeProgress -or (($result -match '(?mi)^RESULT:\s*(PASS|PARTIAL)$') -and $evidence -and $evidence -ne 'NONE' -and $after.local_head -ne $before.local_head)

    $state.current_item = $item
    $state.current_phase = if ($item -match '^(P[0-6])\.') { $Matches[1] } else { $null }
    $state.last_snapshot = $after; $state.last_evidence = $evidence; $state.next_action = $next
    $state.last_result = [ordered]@{ exit_code = $exitCode; made_progress = $madeProgress; meaningful_turn = $meaningfulTurn; dry_run = [bool]$DryRun; captured_at_utc = [DateTime]::UtcNow.ToString('o') }

    if (Test-HumanGateResult $result) {
      $state.status = 'HUMAN_GATE_REQUIRED'; $state.stop_reason = 'HUMAN_GATE_REQUIRED'
    } elseif ($exitCode -ne 0 -and (Test-QuotaResult ($result + "`n" + $cliOutput))) {
      $state.status = 'WAITING_QUOTA'; $state.stop_reason = 'WAITING_QUOTA'
      $state.quota_retry_at_utc = [DateTime]::UtcNow.AddMinutes($QuotaRetryMinutes).ToString('o')
    } elseif ($exitCode -ne 0) {
      $state.status = 'PAUSED'; $state.stop_reason = "CODEX_EXIT_$exitCode"
    } elseif ($DryRun) {
      $state.status = 'DRY_RUN'; $state.no_progress_rounds = 0
    } elseif ($meaningfulTurn) {
      $state.status = 'RUNNING'; $state.no_progress_rounds = 0
    } else {
      $state.no_progress_rounds = [int]$state.no_progress_rounds + 1
      if ([int]$state.no_progress_rounds -ge 3) {
        $state.status = 'STOP_NO_PROGRESS'; $state.stop_reason = 'STOP_NO_PROGRESS'
      }
    }
    $state.updated_at_utc = [DateTime]::UtcNow.ToString('o')
    Write-AtomicJson $StatePath $state
    $turnsRun++

    if ($state.status -eq 'WAITING_QUOTA') {
      Start-Sleep -Seconds ($QuotaRetryMinutes * 60)
      continue
    }
    if ($state.stop_reason) { break }
  }
} finally {
  Remove-Item -LiteralPath $LockPath -Force -ErrorAction SilentlyContinue
}
