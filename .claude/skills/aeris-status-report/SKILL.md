---
name: aeris-status-report
description: Produce an accurate P0-P6 blueprint progress report for AERIS (C:\0_JN1_AERIS) plus remote-access health, without guessing from memory. Use whenever asked "還有在跑嗎/what's the progress/依照藍圖P0-P6進度" or before claiming any phase is done.
---

# AERIS Status Report

Never answer a "what's the progress" question from a prior session's memory
or your own earlier claims in this conversation — the truth file is cheap to
re-read and memory goes stale the moment a commit lands. This produces the
same numbers `AERIS_START.ps1` prints, without needing HTTP auth (the
`/api/v1/progress` endpoint now requires a login session since the
multi-user auth system was added — querying the truth engine directly via
local tooling sidesteps that).

## Overall percent + phase breakdown

```powershell
& .venv\Scripts\python.exe -c "
from aeris_runtime import progress_truth
contract = progress_truth.load_contract()
obs = progress_truth.load_observations()
d = progress_truth.evaluate_progress(contract, obs)
print('state', d.state)
print('overall', d.overall_percent)
print('phase', d.phase_percent)
for iid, sc in sorted(d.item_scores.items()):
    if sc != 100:
        print('NOT 100:', iid, sc)
"
```

`d.state` is `VALID`/`UNKNOWN`/`FAIL_CLOSED` — `UNKNOWN` with a high overall
percent is normal and NOT the same as broken (it means "not literally every
item is a fresh signed PASS", not "something regressed"). Only
`FAIL_CLOSED` or a `runtime_candidate_mismatch`-shaped error means real
trouble — see `.claude/skills/aeris-gate/SKILL.md`'s gate-cycle discipline
before assuming that.

## Item-level pass/fail per phase

```powershell
& .venv\Scripts\python.exe -c "
from aeris_runtime.progress_verify import TRUTH_PATH
import json
truth = json.loads(TRUTH_PATH.read_text(encoding='utf-8'))
items = truth['items']
for phase in ['P0','P1','P2','P3','P4','P5','P6']:
    ids = sorted(k for k in items if k.startswith(phase+'.'))
    print(phase, [f'{k}:{items[k][\"result\"]}' for k in ids])
"
```

An item missing entirely from this dict (not even listed) means it has
never passed a check yet, not that it was skipped — cross-reference against
`config/progress_truth.v1.json`'s per-phase item lists to see what's absent.

## Remote-access health (only if asked about phone/tunnel access)

```bash
curl -s -o /dev/null -w "local:%{http_code} " http://127.0.0.1:8765/
Get-Process cloudflared -ErrorAction SilentlyContinue | Select Id,StartTime
```

The quick-tunnel URL rotates every time `cloudflared.exe` restarts. Find the
current one from its log file (path depends on how it was launched that
session — check `.aeris/bin/tunnel*.log` first) rather than assuming the
last one reported in conversation is still live; then diff it against
`outputs/aeris-public-site/index.html`'s `login-link` href and redeploy via
`npx wrangler deploy` (from that directory) if they've drifted apart.

## What NOT to do

Don't call `GET /api/v1/progress` over HTTP as local tooling — it now
returns `401 unauthorized` since the multi-user auth system requires a
session cookie. That 401 is correct behavior, not a bug; use the direct
`progress_truth`/`progress_verify` module calls above instead, which read
the same underlying Evidence without needing a login.
