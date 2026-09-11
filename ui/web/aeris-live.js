(() => {
  'use strict';
  const capabilityScript=document.createElement('script');capabilityScript.src='/assets/capabilities.js';document.head.appendChild(capabilityScript);
  const page=document.body.dataset.page;
  const params=new URLSearchParams(location.search);
  const requested=params.get('theme');
  const visualBaseline=params.get('visual_baseline')==='1';
  if(requested==='dark'||requested==='light'){
    document.documentElement.dataset.theme=requested;
    document.documentElement.style.colorScheme=requested;
  }
  const $=id=>document.getElementById(id);
  const t=value=>window.aerisText?window.aerisText(value):String(value);
  const esc=value=>String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const api=async(path,options={})=>{const r=await fetch(path,{cache:'no-store',headers:{'Content-Type':'application/json'},...options});const body=await r.json().catch(()=>({}));if(!r.ok)throw new Error(body.detail||body.error||`HTTP ${r.status}`);return body};
  const row=(name,meta,badge='')=>`<div class="row"><div><div class="row-name">${esc(t(name))}</div><div class="row-meta">${esc(t(meta))}</div></div>${badge?`<span class="pill">${esc(t(badge))}</span>`:''}</div>`;
  const stateClass=s=>s==='健康'||s==='PASS'?'green':s==='DEGRADED'||s==='STALE'?'amber':s==='BLOCKED'||s==='FAILED'?'rose':'';
  let assetBaseline=null,refreshing=false,lastPod=null;
  const sidebar=document.querySelector('.sidebar');if(sidebar)sidebar.setAttribute('aria-label','AERIS 主要導覽');
  const main=document.querySelector('main.main');if(main)main.id='mainContent';
  const live=$('openingState');if(live){live.setAttribute('role','status');live.setAttribute('aria-live','polite')}
  for(const id of ['project','product','transducer','lifecycle','risk','證據Tier','standardsStrategy','title','需求','假設','證據Needed']){
    const input=$(id),label=input?.closest('.field')?.querySelector('label');if(label)label.htmlFor=id;
  }
  if($('roleQuery'))$('roleQuery').setAttribute('aria-label','搜尋角色');

  async function dashboard(){
    const [s,svc,machine,roles,workflows,audit,maturity,standards]=await Promise.all([
      api('/api/v1/status'),api('/api/v1/services'),api('/api/v1/machine'),api('/api/v1/roles'),
      api('/api/v1/workflows'),api('/api/v1/audit?limit=12'),api('/api/v1/maturity'),api('/api/v1/standards?q=')]);
    $('openingState').textContent=t(s.company_opening_state);$('sidebarState').textContent=t(s.company_opening_state);
    $('runtimeMode').textContent=t(String(s.runtime_mode).toUpperCase());$('offlineState').textContent=s.local_provider_ready?'本機模型服務已就緒':'本機模型服務受限';
    $('modelName').textContent=s.local_model||'尚未設定';$('modelState').textContent=s.local_provider_ready?'就緒':'受限';
    $('roleCount').textContent=`${s.role_count} 席位`;$('overviewRoles').textContent=s.role_count;
    const std=standards.standards?.length||0,know=s.knowledge?.documents||0;
    $('assetCount').textContent=`${s.skill_count}/${std}/${know}`;$('assetDetail').textContent='技能／標準中繼資料／知識文件';
    $('workCount').textContent=`${s.control.projects}/${s.control.tasks}/${s.workflow_run_count}`;$('workDetail').textContent='專案／SQLite 任務／工作流程執行紀錄';
    $('expectedState').textContent=t(s.expected_runs?.overall||'UNKNOWN');$('expectedDetail').textContent=`${s.expected_runs?.runs?.length||0} 份預期執行契約`;
    const byName=Object.fromEntries(svc.services.map(x=>[x.service,x]));
    $('rulesTelemetry').textContent=byName['Constitution / 規則']?.reason||'UNKNOWN';$('skillsTelemetry').textContent=byName['Skill + Method 登錄庫']?.reason||'UNKNOWN';
    $('knowledgeTelemetry').textContent=byName['Memory + Knowledge']?.reason||'UNKNOWN';$('evidenceTelemetry').textContent=byName['Evidence Store']?.reason||'UNKNOWN';$('toolsTelemetry').textContent=byName['Free Local Acoustic Baseline']?.reason||'UNKNOWN';
    $('workflowCount').textContent=`${workflows.workflows.length} 筆執行紀錄`;
    $('workflowRuns').innerHTML=workflows.workflows.length?workflows.workflows.slice(0,8).map(w=>row(w.workflow_id,`${t(w.state)} · 任務 ${w.task_id}`,w.execution?.skill_id||'尚無技能')).join(''):'<div class="empty">尚無工作流程執行紀錄</div>';
    $('watchdogState').textContent=byName['Watchdog Recovery']?.state||'UNKNOWN';
    $('operationsList').innerHTML=row('機器／GPU',byName['Machine / GPU Qualification']?.reason,byName['Machine / GPU Qualification']?.state)+row('監看器',byName['Watchdog Recovery']?.reason,byName['Watchdog Recovery']?.state)+row('離線連續性',byName['Offline Continuity']?.reason,byName['Offline Continuity']?.state)+row('預期執行',byName['Expected-run 健康狀態']?.reason,byName['Expected-run 健康狀態']?.state);
    $('auditState').textContent=byName['Audit Ledger']?.state||'UNKNOWN';
    $('trustList').innerHTML=row('稽核',byName['Audit Ledger']?.reason,byName['Audit Ledger']?.state)+row('證據',byName['Evidence Store']?.reason,byName['Evidence Store']?.state)+row('驗證',byName['驗證 Engine']?.reason,byName['驗證 Engine']?.state)+row('產品階段',maturity.product_stage||'UNKNOWN','儀表板 ≠ 真值');
    $('auditList').innerHTML=audit.records.map(x=>row(t(x.event_type||x.type||'事件'),x.timestamp_utc||x.timestamp||'',x.actor||'')).join('')||'<div class="empty">尚無稽核紀錄</div>';
    const counts={};Object.values(maturity.capabilities||{}).forEach(x=>counts[x.state]=(counts[x.state]||0)+1);
    $('maturityList').innerHTML=Object.entries(counts).sort().map(([k,v])=>row(k,`${v} capabilities`,k)).join('');
    const groups=[...new Set(roles.roles.map(r=>r.group))];$('roleGroup').innerHTML='<option value="">全部群組</option>'+groups.map(g=>`<option>${esc(g)}</option>`).join('');
    const renderRoles=()=>{const q=$('roleQuery').value.toLowerCase(),g=$('roleGroup').value;const items=roles.roles.filter(r=>(!q||`${r.id} ${r.name} ${r.group} ${r.display_name||''} ${r.display_group||''} ${r.domain}`.toLowerCase().includes(q))&&(!g||r.group===g));$('roleVisibleCount').textContent=`${items.length} 席角色`;$('roleGrid').innerHTML=items.map(r=>`<div class="role"><div class="role-id">${esc(r.id)}</div><b>${esc(r.display_name||r.name)}</b><div class="role-group">${esc(r.display_group||r.group)} · ${esc(r.execution_state)}</div><small>${esc(r.display_description||'')}</small></div>`).join('')};
    $('roleQuery').oninput=renderRoles;$('roleGroup').onchange=renderRoles;renderRoles();
  }

  function workspacePayload(){
    const title=$('title').value.trim(),requirement=$('需求').value.trim();
    if(!title||!requirement)throw new Error('工程目標與需求為必填');
    const metadata={product:$('product').value,transducer:$('transducer').value,lifecycle:$('lifecycle').value,evidence_tier:$('證據Tier').value,standards_strategy:$('standardsStrategy').value,requirement,hypothesis:$('假設').value.trim(),evidence_needed:$('證據Needed').value.trim()};
    const description=[`產品：${metadata.product}`,`換能器：${metadata.transducer}`,`生命週期：${metadata.lifecycle}`,`需求：${requirement}`,`假設：${metadata.hypothesis}`,`所需證據：${metadata.evidence_needed}`].join('\n');
    return {project_id:$('project').value,title,description,risk_level:$('risk').value,auto_pod:true,max_roles:15,metadata,create_workflow:true,actor:'AERIS 本機工作區'};
  }
  async function loadWorkspace(){
    const [status,projects,tasks]=await Promise.all([api('/api/v1/status'),api('/api/v1/projects'),api('/api/v1/tasks')]);
    $('openingState').textContent=t(status.company_opening_state);$('sidebarState').textContent=t(status.company_opening_state);
    const selected=$('project').value;$('project').innerHTML=projects.projects.map(p=>`<option value="${esc(p.id)}">${esc(p.name)} (${p.task_count})</option>`).join('');if(selected)$('project').value=selected;
    $('taskList').innerHTML=tasks.tasks.length?tasks.tasks.map(task=>row(task.title,`${task.id} · ${t(task.state)} · ${task.risk_level} · 工作流程 ${task.workflow_id||'尚未建立'}`,task.metadata?.product||'')).join(''):'<div class="empty">尚無 SQLite 任務</div>';
  }
  async function routePod(){
    const p=workspacePayload(),transducer=({speaker:'揚聲器',microphone:'麥克風',both:'Both'})[p.metadata.transducer]||p.metadata.transducer;
    const needed=['engineering-requirements'];
    if(['揚聲器','Both'].includes(transducer))needed.push('lumped-speaker');
    if(['麥克風','Both'].includes(transducer))needed.push('microphone-sensitivity');
    lastPod=await api('/api/v1/capabilities/pod',{method:'POST',body:JSON.stringify({product:p.metadata.product,transducer,lifecycle:p.metadata.lifecycle,risk:p.risk_level,requirement:p.metadata.requirement,required_evidence:[p.metadata.evidence_needed||'封存數值分析'],needed_skills:needed,available_tools:['FREE_LOCAL_BASELINE']})});
    $('podSize').textContent=`${lastPod.pod_size} 專家`;
    $('podDesc').textContent=`${p.metadata.product} · ${transducer} · ${p.metadata.lifecycle} · ${p.risk_level} · ${lastPod.planner}`;
    $('podGrid').innerHTML=lastPod.roles.map((r,i)=>`<div class="person"><b>${i===0?'主責 · ':''}${esc(r.id)} ${esc(r.display_name||r.name)}</b>${esc(r.display_group||r.group)} · ${esc(t(r.selection_reason))}</div>`).join('');
    $('需求看板').textContent=p.metadata.requirement;$('假設看板').textContent=p.metadata.hypothesis||'尚未提供';$('證據看板').textContent=p.metadata.evidence_needed||'尚未提供';
  }
  async function createWorkspaceTask(){const p=workspacePayload();const result=await api('/api/v1/tasks',{method:'POST',body:JSON.stringify(p)});$('task結果').textContent=`已建立 SQLite ${result.task.id} 與工作流程 ${result.workflow.workflow_id}；狀態 ${result.workflow.state}，尚未執行或驗證。`;await loadWorkspace()}

  async function services(){const [status,data]=await Promise.all([api('/api/v1/status'),api('/api/v1/services')]);$('openingState').textContent=t(status.company_opening_state);$('sidebarState').textContent=t(status.company_opening_state);$('generatedAt').textContent=visualBaseline?'即時 API 評估／可變動':`最近 API 評估 ${data.generated_at_utc}`;$('serviceCount').textContent=`${data.services.length} 項觀測服務`;
    $('planeCards').innerHTML=data.planes.map(p=>`<div class="layer"><h3>${esc(t(p))}</h3>${data.services.filter(x=>x.plane===p).map(x=>`<div class="svc"><b>${esc(t(x.service))}</b><small>${esc(t(x.state))} · ${esc(t(x.reason))}</small></div>`).join('')}</div>`).join('');
    $('serviceRows').innerHTML=data.services.map(x=>`<tr><td><b>${esc(t(x.service))}</b></td><td>${esc(t(x.plane))}</td><td><span class="pill ${stateClass(x.state)}">${esc(t(x.state))}</span><div class="row-meta">${esc(t(x.reason))}</div></td><td>${esc(x.evidence_ref||'無證據參照')}<div class="row-meta">${esc(visualBaseline?'可變動':(x.last_update_utc||'UNKNOWN'))}</div></td><td>${esc(t(x.capability_maturity))}</td></tr>`).join('');
    $('stateCounts').innerHTML=Object.entries(data.state_counts).map(([s,n])=>`<span class="pill ${stateClass(s)}">${esc(s)} · ${n}</span>`).join('');
  }

  async function refresh(){if(refreshing)return;refreshing=true;try{if(page==='dashboard')await dashboard();else if(page==='workspace')await loadWorkspace();else if(page==='services')await services()}catch(e){const target=$('openingState');if(target)target.textContent=`API 錯誤 · ${e.message}`}finally{refreshing=false}}
  async function assetCheck(){try{const paths=[location.pathname,'/assets/aeris.css','/assets/aeris-theme.js','/assets/aeris-live.js','/assets/capabilities.js'];const text=await Promise.all(paths.map(async p=>{const r=await fetch(p,{cache:'no-store'});return `${r.status}:${await r.text()}`}));const snap=text.join('\n--AERIS--\n');if(assetBaseline!==null&&assetBaseline!==snap)location.reload();assetBaseline=snap}catch(_){}}
  document.querySelectorAll('[data-refresh]').forEach(b=>b.addEventListener('click',refresh));
  if(page==='workspace'){$('routeBtn').addEventListener('click',()=>routePod().catch(e=>$('task結果').textContent=e.message));$('createBtn').addEventListener('click',()=>createWorkspaceTask().catch(e=>$('task結果').textContent=e.message));$('resetBtn').addEventListener('click',()=>location.reload())}
  addEventListener('focus',refresh);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});if(!visualBaseline)setInterval(refresh,10000);setInterval(assetCheck,15000);refresh();assetCheck();
})();
