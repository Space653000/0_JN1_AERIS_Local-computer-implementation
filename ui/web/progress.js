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
  if (percent === null || percent === undefined) return 'tier-none';
  if (percent >= 90) return 'tier-done';
  if (percent >= 40) return 'tier-mid';
  if (percent > 0) return 'tier-low';
  return 'tier-none';
}

function renderRing(percent) {
  const fill = document.getElementById('ringFill');
  const safe = Math.max(0, Math.min(100, percent || 0));
  fill.style.strokeDashoffset = String(RING_CIRCUMFERENCE * (1 - safe / 100));
  fill.classList.remove('tier-done', 'tier-mid', 'tier-low', 'tier-none');
  const tier = tierClass(safe);
  fill.style.stroke = {
    'tier-done': 'var(--green)', 'tier-mid': 'var(--accent)',
    'tier-low': 'var(--amber)', 'tier-none': 'var(--rose)',
  }[tier];
}

function renderPhaseBars(phasePercent) {
  const rows = Object.entries(phasePercent).map(([phase, percent]) => {
    const safe = percent === null || percent === undefined ? 0 : percent;
    const pair = PHASE_LABELS[phase] || [phase, phase];
    const label = L(pair[0], pair[1]);
    return `<div class="phase-bar-row">
      <span class="phase-bar-id">${phase}</span>
      <span class="phase-bar-track" title="${label}"><span class="phase-bar-fill ${tierClass(percent)}" style="width:${safe}%"></span></span>
      <span class="phase-bar-pct">${percent === null || percent === undefined ? 'UNKNOWN' : safe + '%'}</span>
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

async function load() {
  const r = await fetch('/api/v1/progress', { cache: 'no-store' });
  const d = await r.json();
  const locale = L('zh-TW', 'en-US');
  document.getElementById('state').textContent =
    L('已更新 ', 'Updated ') + new Date(d.generated_at_utc).toLocaleString(locale);
  document.getElementById('overallPercent').textContent = d.overall_percent + '%';
  renderRing(d.overall_percent);
  renderPhaseBars(d.phase_percent);
  document.getElementById('nextAction').textContent = renderNextAction(d.next_action);
  document.getElementById('blockers').textContent = d.blockers.length ? d.blockers.join(L('、', ', ')) : L('無', 'None');
  const truthEl = document.getElementById('truthState');
  truthEl.textContent = d.truth_state;
  truthEl.className = 'pill' + (d.truth_state === 'FAIL_CLOSED' ? ' rose' : d.truth_state === 'VALID' ? ' green' : ' amber');
  document.getElementById('shaLine').textContent = (d.implementation_sha || 'UNKNOWN').slice(0, 12) +
    (d.runtime_candidate_aligned ? L('（與程式碼對齊）', ' (aligned with source)') : L('（與程式碼不一致）', ' (mismatched with source)'));
  renderItems(d.items);
}

load();
setInterval(load, 10000);
window.addEventListener('focus', load);
document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
document.getElementById('refreshBtn')?.addEventListener('click', load);
