(() => {
  'use strict';
  const page=document.body.dataset.page;
  const params=new URLSearchParams(location.search);
  const requested=params.get('theme');
  const visualBaseline=params.get('visual_baseline')==='1';
  if(requested==='dark'||requested==='light'){
    document.documentElement.dataset.theme=requested;
    document.documentElement.style.colorScheme=requested;
  }
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const api=async(path,options={})=>{const r=await fetch(path,{cache:'no-store',headers:{'Content-Type':'application/json'},...options});const body=await r.json().catch(()=>({}));if(!r.ok)throw new Error(body.detail||body.error||`HTTP ${r.status}`);return body};
  const row=(name,meta,badge='')=>`<div class="row"><div><div class="row-name">${esc(name)}</div><div class="row-meta">${esc(meta)}</div></div>${badge?`<span class="pill">${esc(badge)}</span>`:''}</div>`;
  const stateClass=s=>s==='HEALTHY'||s==='PASS'?'green':s==='DEGRADED'||s==='STALE'?'amber':s==='BLOCKED'||s==='FAILED'?'rose':'';
  let assetBaseline=null,refreshing=false,lastPod=null;
  const sidebar=document.querySelector('.sidebar');if(sidebar)sidebar.setAttribute('aria-label','AERIS 主要導覽');
  const main=document.querySelector('main.main');if(main)main.id='mainContent';
  const live=$('openingState');if(live){live.setAttribute('role','status');live.setAttribute('aria-live','polite')}
  for(const id of ['project','product','transducer','lifecycle','risk','evidenceTier','standardsStrategy','title','requirement','hypothesis','evidenceNeeded']){
    const input=$(id),label=input?.closest('.field')?.querySelector('label');if(label)label.htmlFor=id;
  }
  if($('roleQuery'))$('roleQuery').setAttribute('aria-label','搜尋角色');

  async function dashboard(){
    const [s,svc,machine,roles,workflows,audit,maturity,standards]=await Promise.all([
      api('/api/v1/status'),api('/api/v1/services'),api('/api/v1/machine'),api('/api/v1/roles'),
      api('/api/v1/workflows'),api('/api/v1/audit?limit=12'),api('/api/v1/maturity'),api('/api/v1/standards?q=')]);
    $('openingState').textContent=s.company_opening_state;$('sidebarState').textContent=s.company_opening_state;
    $('runtimeMode').textContent=String(s.runtime_mode).toUpperCase();$('offlineState').textContent=s.local_provider_ready?'LOCAL PROVIDER READY':'LOCAL PROVIDER DEGRADED';
    $('modelName').textContent=s.local_model||'NOT_CONFIGURED';$('modelState').textContent=s.local_provider_ready?'READY':'DEGRADED';
    $('roleCount').textContent=`${s.role_count} 席位`;$('overviewRoles').textContent=s.role_count;
    const std=standards.standards?.length||0,know=s.knowledge?.documents||0;
    $('assetCount').textContent=`${s.skill_count}/${std}/${know}`;$('assetDetail').textContent='Skills / Standards metadata / Knowledge docs';
    $('workCount').textContent=`${s.control.projects}/${s.control.tasks}/${s.workflow_run_count}`;$('workDetail').textContent='Projects / SQLite tasks / Workflow runs';
    $('expectedState').textContent=s.expected_runs?.overall||'UNKNOWN';$('expectedDetail').textContent=`${s.expected_runs?.runs?.length||0} expected-run contracts`;
    const byName=Object.fromEntries(svc.services.map(x=>[x.service,x]));
    $('rulesTelemetry').textContent=byName['Constitution / Rules']?.reason||'UNKNOWN';$('skillsTelemetry').textContent=byName['Skill + Method Registry']?.reason||'UNKNOWN';
    $('knowledgeTelemetry').textContent=byName['Memory + Knowledge']?.reason||'UNKNOWN';$('evidenceTelemetry').textContent=byName['Evidence Store']?.reason||'UNKNOWN';$('toolsTelemetry').textContent=byName['Free Local Acoustic Baseline']?.reason||'UNKNOWN';
    $('workflowCount').textContent=`${workflows.workflows.length} runs`;
    $('workflowRuns').innerHTML=workflows.workflows.length?workflows.workflows.slice(0,8).map(w=>row(w.workflow_id,`${w.state} · task ${w.task_id}`,w.execution?.skill_id||'NO SKILL')).join(''):'<div class="empty">尚無 instantiated workflow run</div>';
    $('watchdogState').textContent=byName['Watchdog Recovery']?.state||'UNKNOWN';
    $('operationsList').innerHTML=row('Machine / GPU',byName['Machine / GPU Qualification']?.reason,byName['Machine / GPU Qualification']?.state)+row('Watchdog',byName['Watchdog Recovery']?.reason,byName['Watchdog Recovery']?.state)+row('Offline',byName['Offline Continuity']?.reason,byName['Offline Continuity']?.state)+row('Expected runs',byName['Expected-run Health']?.reason,byName['Expected-run Health']?.state);
    $('auditState').textContent=byName['Audit Ledger']?.state||'UNKNOWN';
    $('trustList').innerHTML=row('Audit',byName['Audit Ledger']?.reason,byName['Audit Ledger']?.state)+row('Evidence',byName['Evidence Store']?.reason,byName['Evidence Store']?.state)+row('Verification',byName['Verification Engine']?.reason,byName['Verification Engine']?.state)+row('Product stage',maturity.product_stage||'UNKNOWN','Dashboard ≠ Truth');
    $('auditList').innerHTML=audit.records.map(x=>row(x.event_type||x.type||'EVENT',x.timestamp_utc||x.timestamp||'',x.actor||'')).join('')||'<div class="empty">尚無 audit record</div>';
    const counts={};Object.values(maturity.capabilities||{}).forEach(x=>counts[x.state]=(counts[x.state]||0)+1);
    $('maturityList').innerHTML=Object.entries(counts).sort().map(([k,v])=>row(k,`${v} capabilities`,k)).join('');
    const groups=[...new Set(roles.roles.map(r=>r.group))];$('roleGroup').innerHTML='<option value="">全部群組</option>'+groups.map(g=>`<option>${esc(g)}</option>`).join('');
    const renderRoles=()=>{const q=$('roleQuery').value.toLowerCase(),g=$('roleGroup').value;const items=roles.roles.filter(r=>(!q||`${r.id} ${r.name} ${r.group} ${r.domain}`.toLowerCase().includes(q))&&(!g||r.group===g));$('roleVisibleCount').textContent=`${items.length} roles`;$('roleGrid').innerHTML=items.map(r=>`<div class="role"><div class="role-id">${esc(r.id)}</div><b>${esc(r.name)}</b><div class="role-group">${esc(r.group)} · ${esc(r.execution_state)}</div></div>`).join('')};
    $('roleQuery').oninput=renderRoles;$('roleGroup').onchange=renderRoles;renderRoles();
  }

  function workspacePayload(){
    const title=$('title').value.trim(),requirement=$('requirement').value.trim();
    if(!title||!requirement)throw new Error('Engineering Objective 與 Requirement 為必填');
    const metadata={product:$('product').value,transducer:$('transducer').value,lifecycle:$('lifecycle').value,evidence_tier:$('evidenceTier').value,standards_strategy:$('standardsStrategy').value,requirement,hypothesis:$('hypothesis').value.trim(),evidence_needed:$('evidenceNeeded').value.trim()};
    const description=[`Product: ${metadata.product}`,`Transducer: ${metadata.transducer}`,`Lifecycle: ${metadata.lifecycle}`,`Requirement: ${requirement}`,`Hypothesis: ${metadata.hypothesis}`,`Evidence Needed: ${metadata.evidence_needed}`].join('\n');
    return {project_id:$('project').value,title,description,risk_level:$('risk').value,auto_pod:true,max_roles:15,metadata,create_workflow:true,actor:'AERIS Local Workspace'};
  }
  async function loadWorkspace(){
    const [status,projects,tasks]=await Promise.all([api('/api/v1/status'),api('/api/v1/projects'),api('/api/v1/tasks')]);
    $('openingState').textContent=status.company_opening_state;$('sidebarState').textContent=status.company_opening_state;
    const selected=$('project').value;$('project').innerHTML=projects.projects.map(p=>`<option value="${esc(p.id)}">${esc(p.name)} (${p.task_count})</option>`).join('');if(selected)$('project').value=selected;
    $('taskList').innerHTML=tasks.tasks.length?tasks.tasks.map(t=>row(t.title,`${t.id} · ${t.state} · ${t.risk_level} · workflow ${t.workflow_id||'NOT_CREATED'}`,t.metadata?.product||'')).join(''):'<div class="empty">尚無 SQLite task</div>';
  }
  async function routePod(){const p=workspacePayload();const query=`${p.metadata.product} ${p.metadata.transducer} ${p.description}`;lastPod=await api('/api/v1/pods/plan',{method:'POST',body:JSON.stringify({query,max_roles:15})});$('podSize').textContent=`${lastPod.pod_size} specialists`;$('podDesc').textContent=`${p.metadata.product} · ${p.metadata.transducer} · ${p.metadata.lifecycle} · ${p.risk_level} · ${lastPod.planner}`;$('podGrid').innerHTML=lastPod.roles.map((r,i)=>`<div class="person"><b>${i===0?'LEAD · ':''}${esc(r.id)} ${esc(r.name)}</b>${esc(r.group)} · ${esc(r.domain)}</div>`).join('');$('requirementBoard').textContent=p.metadata.requirement;$('hypothesisBoard').textContent=p.metadata.hypothesis||'尚未提供';$('evidenceBoard').textContent=p.metadata.evidence_needed||'尚未提供'}
  async function createWorkspaceTask(){const p=workspacePayload();const result=await api('/api/v1/tasks',{method:'POST',body:JSON.stringify(p)});$('taskResult').textContent=`已建立 SQLite ${result.task.id} 與 Workflow ${result.workflow.workflow_id}；狀態 ${result.workflow.state}，尚未執行或驗證。`;await loadWorkspace()}

  async function services(){const [status,data]=await Promise.all([api('/api/v1/status'),api('/api/v1/services')]);$('openingState').textContent=status.company_opening_state;$('sidebarState').textContent=status.company_opening_state;$('generatedAt').textContent=visualBaseline?'Last API assessment · MUTABLE':`Last API assessment ${data.generated_at_utc}`;$('serviceCount').textContent=`${data.services.length} observed services`;
    $('planeCards').innerHTML=data.planes.map(p=>`<div class="layer"><h3>${esc(p)}</h3>${data.services.filter(x=>x.plane===p).map(x=>`<div class="svc"><b>${esc(x.service)}</b><small>${esc(x.state)} · ${esc(x.reason)}</small></div>`).join('')}</div>`).join('');
    $('serviceRows').innerHTML=data.services.map(x=>`<tr><td><b>${esc(x.service)}</b></td><td>${esc(x.plane)}</td><td><span class="pill ${stateClass(x.state)}">${esc(x.state)}</span><div class="row-meta">${esc(x.reason)}</div></td><td>${esc(x.evidence_ref||'NO EVIDENCE REF')}<div class="row-meta">${esc(visualBaseline?'MUTABLE':(x.last_update_utc||'UNKNOWN'))}</div></td><td>${esc(x.capability_maturity)}</td></tr>`).join('');
    $('stateCounts').innerHTML=Object.entries(data.state_counts).map(([s,n])=>`<span class="pill ${stateClass(s)}">${esc(s)} · ${n}</span>`).join('');
  }

  async function refresh(){if(refreshing)return;refreshing=true;try{if(page==='dashboard')await dashboard();else if(page==='workspace')await loadWorkspace();else if(page==='services')await services()}catch(e){const target=$('openingState');if(target)target.textContent=`API ERROR · ${e.message}`}finally{refreshing=false}}
  async function assetCheck(){try{const paths=[location.pathname,'/assets/aeris.css','/assets/aeris-theme.js','/assets/aeris-live.js'];const text=await Promise.all(paths.map(async p=>{const r=await fetch(p,{cache:'no-store'});return `${r.status}:${await r.text()}`}));const snap=text.join('\n--AERIS--\n');if(assetBaseline!==null&&assetBaseline!==snap)location.reload();assetBaseline=snap}catch(_){}}
  document.querySelectorAll('[data-refresh]').forEach(b=>b.addEventListener('click',refresh));
  if(page==='workspace'){$('routeBtn').addEventListener('click',()=>routePod().catch(e=>$('taskResult').textContent=e.message));$('createBtn').addEventListener('click',()=>createWorkspaceTask().catch(e=>$('taskResult').textContent=e.message));$('resetBtn').addEventListener('click',()=>location.reload())}
  addEventListener('focus',refresh);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});if(!visualBaseline)setInterval(refresh,10000);setInterval(assetCheck,15000);refresh();assetCheck();
})();
