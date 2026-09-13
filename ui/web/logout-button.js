(function () {
  async function inject() {
    const bar = document.querySelector('.sidebar-utilities');
    if (!bar || bar.querySelector('[data-logout]')) return;

    try {
      const r = await fetch('/api/v1/auth/status', { cache: 'no-store' });
      const status = await r.json();
      if (status.role === 'owner' && document.body.dataset.page !== 'admin') {
        const adminBtn = document.createElement('a');
        adminBtn.className = 'utility-btn';
        adminBtn.href = '/admin';
        adminBtn.innerHTML = '<span class="nav-icon">◈</span><span>帳號管理</span>';
        bar.appendChild(adminBtn);
      }
    } catch (e) {}

    const btn = document.createElement('button');
    btn.className = 'utility-btn';
    btn.setAttribute('data-logout', '');
    btn.innerHTML = '<span class="nav-icon">⇥</span><span>登出</span>';
    btn.addEventListener('click', async () => {
      try { await fetch('/api/v1/auth/logout', { method: 'POST' }); } catch (e) {}
      window.location.href = '/login';
    });
    bar.appendChild(btn);
  }
  if (document.querySelector('.sidebar-utilities')) {
    inject();
  } else {
    new MutationObserver((_, obs) => {
      if (document.querySelector('.sidebar-utilities')) { inject(); obs.disconnect(); }
    }).observe(document.body, { childList: true, subtree: true });
  }
})();
