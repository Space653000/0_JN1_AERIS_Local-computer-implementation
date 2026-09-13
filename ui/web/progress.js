const RING_CIRCUMFERENCE = 2 * Math.PI * 52;
const PHASE_LABELS = {
  P0: ['基礎建設', 'Foundation'], P1: ['Kairos UX', 'Kairos UX'], P2: ['進度引擎', 'Progress Engine'],
  P3: ['黃金工程師', 'Golden Engineer'], P4: ['技能教學', 'Skill Teaching'],
  P5: ['工程工廠', 'Engineering Factory'], P6: ['公司整合', 'Company Integration'],
};
const L = (zh, en) => (window.AERIS_LANG === 'en' ? en : zh);

function renderNextAction(nextAction) {
  if (nextAction.kind === 'fail_closed') {
    return L('修復 runtime/candidate 對齊或無效 Evidence 後重新驗證（見 truth_errors）',
      'Fix the runtime/candidate mismatch or invalid Evidence, then re-verify (see truth_errors)');
  }
  if (nextAction.kind === 'complete') {
    return L('P0-P6 全部項目已通過', 'All P0-P6 items have passed');
  }
  const ids = nextAction.pending_ids.join(L('、', ', '));
  return L(`完成 ${nextAction.phase} 未通過項目：${ids}`, `Finish ${nextAction.phase}'s pending items: ${ids}`);
}

function tierClass(percent) {
  if (percent === null || percent === undefined) return 'tier-unknown';
  if (percent >= 90) return 'tier-done';
  if (percent >= 40) return 'tier-mid';
  if (percent > 0) return 'tier-low';
  return 'tier-none';
}

function renderRing(percent) {
  const fill = document.getElementById('ringFill');
  const known = percent !== null && percent !== undefined;
  const safe = Math.max(0, Math.min(100, known ? percent : 0));
  fill.style.strokeDashoffset = String(RING_CIRCUMFERENCE * (1 - (known ? safe : 100) / 100));
  fill.classList.remove('tier-done', 'tier-mid', 'tier-low', 'tier-none', 'tier-unknown');
  const tier = tierClass(percent);
  fill.classList.add(tier);
  fill.style.stroke = known ? {
    'tier-done': 'var(--green)', 'tier-mid': 'var(--accent)',
    'tier-low': 'var(--amber)', 'tier-none': 'var(--rose)',
  }[tier] : 'var(--border-strong)';
}

function renderPhaseBars(phasePercent) {
  const rows = Object.entries(phasePercent).map(([phase, percent]) => {
    const known = percent !== null && percent !== undefined;
    const pair = PHASE_LABELS[phase] || [phase, phase];
    const label = L(pair[0], pair[1]);
    return `<div class="phase-bar-row">
      <span class="phase-bar-id">${phase}</span>
      <span class="phase-bar-track" title="${label}"><span class="phase-bar-fill ${tierClass(percent)}" style="width:${known ? percent : 100}%"></span></span>
      <span class="phase-bar-pct">${known ? percent + '%' : 'UNKNOWN'}</span>
    </div>`;
  });
  document.getElementById('phaseBars').innerHTML = rows.join('');
}

function renderItems(items) {
  const passCount = items.filter(x => x.state === 'PASS').length;
  document.getElementById('itemsSummary').textContent =
    L(`${passCount} / ${items.length} 項已通過`, `${passCount} / ${items.length} items passed`);
  document.getElementById('items').innerHTML = items.map(x => `<div class="progress-item">
      <b class="progress-item-id">${x.id}</b>
      <span class="state-badge ${x.state}">${x.state} · ${x.percent}%</span>
      <small class="progress-item-evidence">${x.evidence || L('無證據', 'No evidence')} · SHA ${x.sha || 'UNKNOWN'}</small>
    </div>`).join('');
}

function renderHistory(points) {
  const el = document.getElementById('historyChart');
  if (!points.length) {
    el.innerHTML = `<div class="history-empty">${L('尚無歷史紀錄', 'No history yet')}</div>`;
    return;
  }
  const locale = L('zh-TW', 'en-US');
  el.innerHTML = points.map(p => {
    const pct = p.overall_percent;
    const when = new Date(p.captured_at_utc).toLocaleString(locale);
    const title = `${p.candidate_sha.slice(0, 10)} · ${pct}% · ${when}`;
    return `<div class="history-bar-wrap" title="${title}">
      <div class="history-bar ${tierClass(pct)}" style="height:${Math.max(pct, 2)}%"></div>
    </div>`;
  }).join('');
}

async function loadHistory() {
  try {
    const r = await fetch('/api/v1/progress/history', { cache: 'no-store' });
    if (!r.ok) return renderHistory([]);
    const d = await r.json();
    renderHistory(d.points || []);
  } catch (e) {
    renderHistory([]);
  }
}

const LAST_GOOD_KEY = 'aeris_progress_last_good';

function saveLastGood(d) {
  try {
    localStorage.setItem(LAST_GOOD_KEY, JSON.stringify({ d, savedAt: Date.now() }));
  } catch (e) {}
}

function loadLastGood() {
  try {
    const raw = localStorage.getItem(LAST_GOOD_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function renderStaleBanner(savedAt) {
  const el = document.getElementById('staleBanner');
  if (!el) return;
  if (savedAt === null) { el.hidden = true; return; }
  const locale = L('zh-TW', 'en-US');
  el.hidden = false;
  el.textContent = L(
    `目前正在重新驗證中，下方為上次成功驗證的結果（${new Date(savedAt).toLocaleString(locale)}），數字不會因此消失或歸零。`,
    `Re-verification in progress -- showing the last successfully verified result (${new Date(savedAt).toLocaleString(locale)}); numbers won't blank out during this window.`
  );
}

function renderProgressPayload(d) {
  const locale = L('zh-TW', 'en-US');
  document.getElementById('state').textContent =
    L('已更新 ', 'Updated ') + new Date(d.generated_at_utc).toLocaleString(locale);
  document.getElementById('overallPercent').textContent = d.overall_percent + '%';
  renderRing(d.overall_percent);
  renderPhaseBars(d.phase_percent);
  document.getElementById('nextAction').textContent = renderNextAction(d.next_action);
  document.getElementById('blockers').textContent = d.blockers.length ? d.blockers.join(L('、', ', ')) : L('無', 'None');
  document.getElementById('shaLine').textContent = (d.implementation_sha || 'UNKNOWN').slice(0, 12) +
    (d.runtime_candidate_aligned ? L('（與程式碼對齊）', ' (aligned with source)') : L('（與程式碼不一致）', ' (mismatched with source)'));
  renderItems(d.items);
}

async function load() {
  const r = await fetch('/api/v1/progress', { cache: 'no-store' });
  const d = await r.json();

  // The truth-state pill always reflects the REAL current status --
  // never hidden or faked, per this project's fail-closed-and-honest
  // design. Only the reference numbers below it fall back to the last
  // verified snapshot instead of blanking to null/UNKNOWN, so a
  // transient re-verification window (right after every commit/restart)
  // doesn't look like the system broke.
  const truthEl = document.getElementById('truthState');
  truthEl.textContent = d.truth_state;
  truthEl.className = 'pill' + (d.truth_state === 'FAIL_CLOSED' ? ' rose' : d.truth_state === 'VALID' ? ' green' : ' amber');

  if (d.overall_percent !== null && d.overall_percent !== undefined) {
    renderProgressPayload(d);
    renderStaleBanner(null);
    saveLastGood(d);
    return;
  }
  const cached = loadLastGood();
  if (cached) {
    renderProgressPayload(cached.d);
    renderStaleBanner(cached.savedAt);
  } else {
    // No prior good snapshot exists yet (e.g. first-ever load) -- there
    // is genuinely nothing honest to show but UNKNOWN.
    renderProgressPayload(d);
    renderStaleBanner(null);
  }
}

load();
loadHistory();
setInterval(load, 10000);
setInterval(loadHistory, 60000);
window.addEventListener('focus', load);
document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
document.getElementById('refreshBtn')?.addEventListener('click', () => { load(); loadHistory(); });
