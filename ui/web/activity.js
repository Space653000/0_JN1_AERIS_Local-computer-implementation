(()=>{
  const $=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const t=v=>window.aerisText?window.aerisText(v):String(v??'');
  const api=async path=>{const r=await fetch(path,{cache:'no-store'});const body=await r.json().catch(()=>({}));if(!r.ok)throw new Error(body.detail||body.error||`HTTP ${r.status}`);return body};
  const VERIFIED_RESULTS=new Set(['PASS','FAIL','BLOCKED','FAILED']);
  const isVerifiedRecord=r=>{
    const p=r.payload||{};
    if(typeof p.success==='boolean')return true;
    if(typeof p.result==='string'&&VERIFIED_RESULTS.has(p.result.toUpperCase()))return true;
    if(typeof p.state==='string'&&VERIFIED_RESULTS.has(p.state.toUpperCase()))return true;
    return false;
  };
  let offset=0,total=0,rows=[];
  function summarize(payload){
    try{const s=JSON.stringify(payload??{});return s.length>160?s.slice(0,160)+'…':s}catch(_){return ''}
  }
  function render(){
    const q=$('filterQuery').value.trim().toLowerCase(),kind=$('filterKind').value;
    const filtered=rows.filter(r=>{
      if(kind==='verified'&&!isVerifiedRecord(r))return false;
      if(kind==='informational'&&isVerifiedRecord(r))return false;
      if(!q)return true;
      return `${r.event_type||''} ${r.actor||''}`.toLowerCase().includes(q);
    });
    $('auditRows').innerHTML=filtered.length?filtered.map(r=>`<tr><td>${esc(r.timestamp_utc||'')}</td><td><b>${esc(r.event_type||'EVENT')}</b></td><td>${esc(r.actor||'')}</td><td>${isVerifiedRecord(r)?'<span class="pill green">有判定</span>':'<span class="pill">資訊</span>'}</td><td class="row-meta">${esc(summarize(r.payload))}</td></tr>`).join(''):'<tr><td colspan="5">尚無符合篩選的事件</td></tr>';
    $('totalCount').textContent=`${total} 筆帳本紀錄 · 已載入 ${rows.length} 筆`;
    $('pageMeta').textContent=rows.length>=total?'已載入全部':`已載入 ${rows.length}／${total}`;
    $('loadMoreBtn').disabled=rows.length>=total;
  }
  async function loadPage(){
    const d=await api(`/api/v1/audit?limit=50&offset=${offset}`);
    total=d.total||0; rows=rows.concat(d.records||[]); offset=rows.length;
    render();
  }
  async function verifyChain(){
    $('chainState').textContent='檢查中…';
    try{
      const d=await api('/api/v1/audit/verify');
      $('chainState').textContent=d.valid?'帳本完整':'帳本鏈斷裂或被竄改';
      $('chainDetail').textContent=`共 ${d.records} 筆紀錄；${(d.errors||[]).length?('發現 '+d.errors.length+' 個問題：'+d.errors.slice(0,3).join('；')):'雜湊鏈逐筆比對通過。'}`;
      $('chainPill').textContent=d.valid?'完整':'異常';
      $('chainPill').className='pill '+(d.valid?'green':'rose');
    }catch(e){$('chainState').textContent='檢查失敗';$('chainDetail').textContent=e.message;$('chainPill').textContent='錯誤';$('chainPill').className='pill rose'}
  }
  async function refreshAll(){
    try{const status=await api('/api/v1/status');$('openingState').textContent=t(status.company_opening_state);$('sidebarState').textContent=t(status.company_opening_state)}catch(_){}
    offset=0;rows=[];await loadPage();
  }
  $('verifyBtn').addEventListener('click',verifyChain);
  $('refreshBtn').addEventListener('click',refreshAll);
  $('loadMoreBtn').addEventListener('click',loadPage);
  $('filterQuery').addEventListener('input',render);
  $('filterKind').addEventListener('change',render);
  refreshAll();
})();
