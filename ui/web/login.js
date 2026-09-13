async function checkStatus() {
  try {
    const r = await fetch('/api/v1/auth/status', { cache: 'no-store' });
    const d = await r.json();
    if (d.authenticated) { window.location.href = '/dashboard'; return; }
    if (!d.credentials_configured) { document.getElementById('noCredentials').hidden = false; }
  } catch (e) {}
}
document.getElementById('loginForm').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const errEl = document.getElementById('loginError');
  errEl.hidden = true;
  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  try {
    const r = await fetch('/api/v1/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
      }),
    });
    if (r.ok) { window.location.href = '/dashboard'; return; }
    const d = await r.json().catch(() => ({}));
    errEl.textContent = d.error === 'no_credentials_configured'
      ? '尚未設定帳號密碼，請先在本機執行 auth set-credentials。'
      : '帳號或密碼錯誤，或嘗試次數過多請稍後再試。';
    errEl.hidden = false;
  } catch (e) {
    errEl.textContent = '無法連線到本機伺服器。';
    errEl.hidden = false;
  } finally {
    btn.disabled = false;
  }
});
checkStatus();
