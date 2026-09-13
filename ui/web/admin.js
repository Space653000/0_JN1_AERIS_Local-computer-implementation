const L = (zh, en) => (window.AERIS_LANG === 'en' ? en : zh);
const PERMISSION_LABELS = {
  dashboard: '儀表板', workspace: '工作區', progress: '進度中心',
  activity: '活動紀錄', services: '服務', capabilities_execute: '可執行技能／建立任務',
};

let grantablePermissions = [];

function renderPermissionChecks() {
  const el = document.getElementById('permissionChecks');
  el.innerHTML = grantablePermissions.map(p => `
    <label class="person" style="cursor:pointer">
      <input type="checkbox" name="perm" value="${p}" style="margin-right:6px">${PERMISSION_LABELS[p] || p}
    </label>`).join('');
}

function renderUsers(users) {
  document.getElementById('userCount').textContent = L(`共 ${users.length} 個帳號`, `${users.length} accounts`);
  document.getElementById('userRows').innerHTML = users.map(u => {
    const perms = u.role === 'owner'
      ? L('全部（擁有者）', 'All (owner)')
      : (u.permissions.map(p => PERMISSION_LABELS[p] || p).join('、') || L('（無）', '(none)'));
    const deleteBtn = u.role === 'owner'
      ? ''
      : `<button class="btn" data-revoke="${u.username}">移除</button>`;
    return `<tr>
      <td>${u.username}</td>
      <td>${u.role === 'owner' ? L('擁有者', 'Owner') : L('授權帳號', 'Granted')}</td>
      <td>${perms}</td>
      <td>${deleteBtn}</td>
    </tr>`;
  }).join('');
  document.querySelectorAll('[data-revoke]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm(L(`確定要移除帳號「${btn.dataset.revoke}」嗎？`, `Remove account "${btn.dataset.revoke}"?`))) return;
      const r = await fetch(`/api/v1/auth/users/${encodeURIComponent(btn.dataset.revoke)}/revoke`, { method: 'POST' });
      if (r.ok) load(); else alert(L('移除失敗', 'Failed to remove'));
    });
  });
}

async function load() {
  const r = await fetch('/api/v1/auth/status', { cache: 'no-store' });
  const status = await r.json();
  if (status.role !== 'owner') {
    document.getElementById('forbiddenNotice').hidden = false;
    document.getElementById('addUserPanel').style.display = 'none';
    document.getElementById('userRows').innerHTML = `<tr><td colspan="4">${L('沒有權限查看', 'No permission to view')}</td></tr>`;
    return;
  }
  const ur = await fetch('/api/v1/auth/users', { cache: 'no-store' });
  if (!ur.ok) return;
  const data = await ur.json();
  grantablePermissions = data.grantable_permissions || [];
  renderPermissionChecks();
  renderUsers(data.users || []);
}

document.getElementById('addUserForm').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const errEl = document.getElementById('addUserError');
  errEl.hidden = true;
  const permissions = Array.from(document.querySelectorAll('input[name="perm"]:checked')).map(i => i.value);
  try {
    const r = await fetch('/api/v1/auth/users', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: document.getElementById('newUsername').value,
        password: document.getElementById('newPassword').value,
        permissions,
      }),
    });
    if (r.ok) {
      document.getElementById('addUserForm').reset();
      load();
      return;
    }
    const d = await r.json().catch(() => ({}));
    errEl.textContent = d.detail || L('新增失敗', 'Failed to add account');
    errEl.hidden = false;
  } catch (e) {
    errEl.textContent = L('無法連線到本機伺服器。', 'Could not reach the local server.');
    errEl.hidden = false;
  }
});

document.getElementById('refreshBtn').addEventListener('click', load);
load();
