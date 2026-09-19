param([int]$Port=8765)
$ErrorActionPreference='Stop'

# This file's own Chinese text was rendering as garbage ("蝑?敺垢隡箸??")
# on this machine: Windows PowerShell 5.1 has no BOM to tell it this .ps1
# is UTF-8, so on a Traditional-Chinese Windows install (console codepage
# 950/Big5) it silently reads these string literals as Big5 bytes instead
# -- corrupting them before Write-Host ever runs. Saving this file with a
# UTF-8 BOM fixes that half; this half fixes the other: the console's own
# output codepage, plus the encoding used to decode the child python.exe
# process's stdout (progress_verify / aeris_launch_checklist.py also print
# Chinese), so every layer agrees on UTF-8 instead of silently disagreeing.
try {
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$Python=Join-Path $Root '.venv\Scripts\python.exe'
if(-not (Test-Path $Python)){
  $cmd=Get-Command python -ErrorAction SilentlyContinue
  if(-not $cmd){ throw 'Python runtime not found. Run AERIS_AUTOPILOT.ps1 first.' }
  $Python=$cmd.Source
}
Set-Location $Root

Write-Host '=== AERIS 本機系統啟動 / Starting AERIS Local System ===' -ForegroundColor Cyan
$listening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($conn in $listening) {
  try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop } catch {}
}
Start-Sleep -Seconds 1
Start-Process -FilePath $Python -ArgumentList '-m','aeris_runtime','company','open','--actor','AERIS_START','--start-supervisor','--port',"$Port" -WindowStyle Hidden

Write-Host '等待後端伺服器啟動 / Waiting for the backend to come up...' -ForegroundColor Cyan
$health = $null
for ($i = 0; $i -lt 30 -and -not $health; $i++) {
  Start-Sleep -Seconds 1
  try { $health = (& $Python -c "import urllib.request,json; print(json.load(urllib.request.urlopen('http://127.0.0.1:$Port/health',timeout=2))['implementation_sha'])" 2>$null) } catch {}
}
if (-not $health) {
  Write-Warning '後端伺服器 30 秒內未能啟動 / Backend did not come up within 30s.'
  exit 1
}

Write-Host '預熱能力矩陣快取（首次計算約需 1-2 分鐘，屬正常現象）/ Warming up the capability matrix cache (first computation legitimately takes ~1-2 min)...' -ForegroundColor Cyan
try {
  & $Python -c @"
import urllib.request
from pathlib import Path
token_path = Path(r'$Root') / '.aeris' / 'state' / '.supervisor-token'
headers = {}
if token_path.is_file():
    headers['X-AERIS-Supervisor-Token'] = token_path.read_text(encoding='utf-8-sig').strip()
urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:$Port/api/v1/capabilities', headers=headers), timeout=240).read()
"@ 2>$null
} catch {}

# Runs one Python step as a real child process with redirected output and
# prints a "still working" heartbeat dot every 5s while it runs, instead of
# leaving the console silent and looking frozen for the several minutes a
# cold-cache full re-verification across 100 roles can legitimately take.
# UTF-8 (BOM-less) is forced on the redirected streams so this machine's
# Traditional-Chinese console codepage never mangles the captured Chinese
# text, matching the [Console]::OutputEncoding fix at the top of this file.
function Invoke-WithHeartbeat {
  param([string[]]$ArgumentList)
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $Python
  foreach ($a in $ArgumentList) { $psi.ArgumentList.Add($a) }
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
  $psi.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)
  $psi.UseShellExecute = $false
  $proc = [System.Diagnostics.Process]::Start($psi)
  $elapsed = 0
  while (-not $proc.HasExited) {
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host -NoNewline "." -ForegroundColor DarkGray
    if ($elapsed % 60 -eq 0) { Write-Host " (${elapsed}s)" -ForegroundColor DarkGray -NoNewline; Write-Host '' }
  }
  Write-Host ''
  $stdout = $proc.StandardOutput.ReadToEnd()
  $stderr = $proc.StandardError.ReadToEnd()
  if ($stdout) { Write-Host $stdout }
  if ($stderr) { Write-Host $stderr -ForegroundColor Yellow }
  return $proc.ExitCode
}

Write-Host '重新驗證全公司工程進度（確保點檢表反映真實狀態，冷啟動時可能需要數分鐘，屬正常現象）/ Refreshing full company progress Evidence (a cold-cache run across 100 roles can legitimately take several minutes)...' -ForegroundColor Cyan
# Trigger the re-verification INSIDE the already-running server via its own
# admin API (/api/v1/progress/reverify) instead of spawning a second,
# separate `python -m aeris_runtime.progress_verify` process. Running both
# at once was found to deadlock: two independent OS processes both doing
# heavy file-based Evidence/audit-ledger reads and writes against the same
# files, with no cross-process lock protecting them (progress_verify.py's
# own _WEB_TRIGGER_LOCK only guards against two triggers within the SAME
# process/server). One real run hung for over an hour instead of the
# expected few minutes. The server already exposes exactly this
# single-flight, same-process trigger for its own Progress Center UI --
# reusing it here removes the second process instead of just working
# around its symptom.
$verifyExit = 1
try {
  $tokenPath = Join-Path $Root '.aeris\state\.supervisor-token'
  $headers = @{}
  if (Test-Path $tokenPath) { $headers['X-AERIS-Supervisor-Token'] = (Get-Content $tokenPath -Raw -Encoding UTF8).Trim() }
  $trigger = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/progress/reverify" -Method Post -Headers $headers -ContentType 'application/json' -Body '{}' -TimeoutSec 10
  if (-not $trigger.started -and $trigger.detail -notlike '*already running*') {
    Write-Warning "重新驗證未能啟動 / Re-verification did not start: $($trigger.detail)"
  }
  $elapsed = 0
  $deadline = 600
  do {
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host -NoNewline "." -ForegroundColor DarkGray
    if ($elapsed % 60 -eq 0) { Write-Host " (${elapsed}s)" }
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/progress/reverify" -Headers $headers -TimeoutSec 10
  } while ($status.running -and $elapsed -lt $deadline)
  Write-Host ''
  if ($status.running) {
    Write-Warning "重新驗證超過 ${deadline}s 仍未完成，略過等待 / Re-verification still running after ${deadline}s, giving up waiting on it (does not block the rest of startup)."
  } elseif ($status.last_result) {
    Write-Host "重新驗證完成：$($status.last_result) / Re-verification finished: $($status.last_result)" -ForegroundColor Cyan
    $verifyExit = 0
  } else {
    Write-Warning '重新驗證狀態不明（伺服器可能在等待期間重啟過）/ Re-verification outcome unknown (the server may have restarted while waiting).'
  }
} catch {
  Write-Warning "無法透過 API 觸發重新驗證，改用點檢表既有結果 / Could not trigger re-verification via the API, falling back to the checklist's own existing result: $($_.Exception.Message)"
}

Write-Host ''
$checklistExit = Invoke-WithHeartbeat -ArgumentList @((Join-Path $Root 'scripts\aeris_launch_checklist.py'), "$Port")

if ($checklistExit -eq 0) {
  Write-Host ''
  Write-Host '系統已就緒，開啟瀏覽器 / System ready, opening browser...' -ForegroundColor Green
  Start-Process "http://127.0.0.1:$Port/dashboard"
} else {
  Write-Host ''
  Write-Warning '有項目未通過點檢，請檢查上方訊息再開啟瀏覽器 / Some checks failed -- review the output above before relying on the UI.'
}

# Best-effort: keep the Cloudflare Quick Tunnel (remote/phone access) alive
# across restarts. Entirely optional and non-fatal -- if cloudflared was
# never installed, or the tunnel fails to (re)start, this must never fail
# the overall startup script. The tunnel's public URL rotates every time
# cloudflared restarts, so it is printed here rather than assumed stable;
# see scripts/aeris_tunnel_status.ps1 to re-check it later without
# restarting anything.
try {
  $cloudflared = Join-Path $Root '.aeris\bin\cloudflared.exe'
  if (Test-Path $cloudflared) {
    $running = Get-Process cloudflared -ErrorAction SilentlyContinue
    if (-not $running) {
      Write-Host ''
      Write-Host '啟動 Cloudflare Tunnel（遠端/手機連線用，非必要功能）/ Starting Cloudflare Tunnel (optional, for remote/phone access)...' -ForegroundColor Cyan
      $tunnelLog = Join-Path $Root '.aeris\bin\tunnel-err.log'
      Start-Process -FilePath $cloudflared -ArgumentList 'tunnel','--url',"http://127.0.0.1:$Port" `
        -RedirectStandardOutput (Join-Path $Root '.aeris\bin\tunnel-out.log') `
        -RedirectStandardError $tunnelLog -WindowStyle Hidden | Out-Null
      $tunnelUrl = $null
      for ($i = 0; $i -lt 15 -and -not $tunnelUrl; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Path $tunnelLog) {
          $match = Select-String -Path $tunnelLog -Pattern 'https://\S+\.trycloudflare\.com' -ErrorAction SilentlyContinue | Select-Object -Last 1
          if ($match) { $tunnelUrl = ([regex]::Match($match.Line, 'https://\S+\.trycloudflare\.com')).Value }
        }
      }
      if ($tunnelUrl) {
        Write-Host "目前隧道網址（每次重啟會改變）/ Current tunnel URL (rotates on every restart): $tunnelUrl" -ForegroundColor Yellow

        # Push the new URL to the public page's own backend (worker.js
        # at outputs/aeris-public-site) so https://aeris.space653000.workers.dev/login
        # always redirects to whichever tunnel is live right now --
        # nobody has to notice the old one died or manually redeploy
        # the page again. Best-effort: the public page still works
        # (with the previous URL on file) if this fails for any reason.
        try {
          $tokenPath = Join-Path $Root '.aeris\state\.tunnel-update-token'
          if (Test-Path $tokenPath) {
            $updateToken = (Get-Content $tokenPath -Raw -Encoding UTF8).Trim()
            $body = @{ url = $tunnelUrl } | ConvertTo-Json -Compress
            Invoke-RestMethod -Uri 'https://aeris.space653000.workers.dev/api/tunnel-url' -Method Post `
              -Headers @{ Authorization = "Bearer $updateToken" } -ContentType 'application/json' -Body $body -TimeoutSec 10 | Out-Null
            Write-Host '已自動更新 https://aeris.space653000.workers.dev/login，外部連結會自動導向這個新網址 / Public login link auto-updated to point at this new URL.' -ForegroundColor Yellow
          } else {
            Write-Warning "找不到 $tokenPath，略過自動更新公開頁面（不影響本機系統）/ Token file not found, skipped updating the public page (does not affect the local system)."
          }
        } catch {
          Write-Warning "自動更新公開頁面失敗，略過（不影響本機系統）/ Failed to auto-update the public page, skipped (does not affect the local system): $($_.Exception.Message)"
        }
      } else {
        Write-Warning 'Cloudflare Tunnel 已啟動但尚未取得網址，請稍後執行 scripts\aeris_tunnel_status.ps1 查看 / Tunnel started but URL not yet available -- check scripts\aeris_tunnel_status.ps1 shortly.'
      }
    }
  }
} catch {
  Write-Warning "Cloudflare Tunnel 啟動略過（非必要功能，不影響本機系統）/ Skipped starting the Cloudflare Tunnel (optional, does not affect the local system): $($_.Exception.Message)"
}

exit $checklistExit
