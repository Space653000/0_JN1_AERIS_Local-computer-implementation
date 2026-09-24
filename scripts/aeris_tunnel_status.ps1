# Prints whether the AERIS Cloudflare Quick Tunnel is currently running and,
# if so, its current public URL -- which rotates every time cloudflared
# restarts, so this must be re-checked rather than assumed from memory.
# See .claude/skills/aeris-status-report/SKILL.md for when to use this.

$ErrorActionPreference = "Continue"
$logPath = "C:\0_JN1_AERIS\.aeris\bin\tunnel-err.log"
$proc = Get-Process cloudflared -ErrorAction SilentlyContinue

if (-not $proc) {
    Write-Host "cloudflared is NOT running."
    if (Test-Path $logPath) {
        Write-Host "Last known URL (from a previous run, likely stale):"
        Select-String -Path $logPath -Pattern "trycloudflare\.com" | Select-Object -Last 1
    }
    exit 1
}

Write-Host "cloudflared IS running (PID $($proc.Id), started $($proc.StartTime))."
if (Test-Path $logPath) {
    $urlLine = Select-String -Path $logPath -Pattern "https://\S+\.trycloudflare\.com" | Select-Object -Last 1
    if ($urlLine) {
        $url = ([regex]::Match($urlLine.Line, "https://\S+\.trycloudflare\.com")).Value
        Write-Host "Current public URL: $url"
        try {
            $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
            Write-Host "Reachability check: HTTP $($resp.StatusCode)"
        } catch {
            Write-Host "Reachability check FAILED: $($_.Exception.Message)"
        }
    } else {
        Write-Host "No tunnel URL found yet in the log -- cloudflared may still be starting up."
    }
} else {
    Write-Host "No log file found at $logPath -- cannot recover the current URL."
}
