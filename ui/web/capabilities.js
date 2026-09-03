(() => {
  'use strict';
  const page=document.body.dataset.page, content=document.querySelector('.content');
  if(!content)return;
  const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  async function api(path,body){const r=await fetch('/api/v1/capabilities'+path,{cache:'no-store',...(body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});const data=await r.json();if(!r.ok)throw Error(data.error||data.detail||r.status);return data;}
  const section=document.createElement('section');section.className='section';section.id='capability-factory';
  section.innerHTML='<div class="section-title"><div><div class="section-kicker">Professional Capability Factory</div><h2>聲學工程能力矩陣</h2></div><span class="pill" id="capSync">等待真實評估</span></div><div class="panel"><p>FREE_LOCAL_BASELINE · L2 本職本機執行證據／L3 獨立角色領域驗收／L4 真實儀器、校正與 Human 驗證。共用 Skill Golden 不等於角色驗收；Memory ≠ Evidence。</p><div id="capCounts" class="chips" aria-live="polite"></div><div id="capKnowledge" class="chips" aria-live="polite">知識來源分類待 API 確認</div><div id="capCoverage" class="list"></div><details><summary>檢查 100 席能力、覆蓋與已知弱點</summary><div id="capRows"></div></details></div>';
  const anchor=document.querySelector('#roles')||document.querySelector('#pod')||document.querySelector('.footer');content.insertBefore(section,anchor);
  const nav=document.querySelector('.sidebar nav');
  if(nav){const link=document.createElement('a');link.href='#capability-factory';link.innerHTML='<span class="nav-icon">◇</span><span class="nav-copy"><b>Capabilities</b><small>能力矩陣／執行分析</small></span>';nav.appendChild(link);}
  if(location.hash==='#capability-factory')section.scrollIntoView();
  let loading=false,roles=[],selectedRole='';
  async function refresh(){if(loading)return;loading=true;try{const matrix=await api('');roles=matrix.roles;
    document.getElementById('capSync').textContent=`L2 以上 ${matrix['100_role_L2']}/${matrix.total_roles}`;
    document.getElementById('capCounts').innerHTML=Object.entries(matrix.maturity_counts).map(([k,v])=>`<span class="chip">${escape(k)}: ${escape(v)}</span>`).join('')+`<span class="chip">Skills ${matrix.total_executable_skills}</span><span class="chip">Methods ${matrix.total_methods}</span><span class="chip">Skill Golden ${matrix.total_golden_cases}</span><span class="chip">Role Golden ${matrix.total_role_golden_cases??'UNKNOWN'}</span><span class="chip">Negative ${matrix.total_negative_cases}</span><span class="chip">Regression ${matrix.total_regression_cases}</span><span class="chip">契約框架 ${matrix.total_roles-matrix.maturity_counts.L0}</span><span class="chip">角色領域驗收 ${matrix.maturity_counts.L3}</span><span class="chip">角色實體驗收 ${matrix.maturity_counts.L4}</span>`;
    document.getElementById('capCoverage').innerHTML=Object.entries(matrix.coverage_by_group).map(([k,v])=>`<div class="row"><b>${escape(k)}</b><span>L2+ ${v.L2_or_higher}/${v.total} · L3 ${v.L3}</span></div>`).join('');
    document.getElementById('capRows').innerHTML=roles.map(r=>`<article class="row"><div><b>${escape(r.id)} ${escape(r.name)} · ${escape(r.level)}</b><p>Skill ${r.coverage.skills}／Method ${r.coverage.methods}／Knowledge ${r.coverage.knowledge}／Golden ${r.coverage.golden}／Evaluated ${r.coverage.evaluated}</p><small>${r.skills.map(escape).join(' · ')}</small><p>${r.known_weaknesses.map(escape).join('；')}</p></div></article>`).join('');
    if(document.getElementById('capRole')){const select=document.getElementById('capRole');const old=select.value;select.innerHTML=roles.map(r=>`<option value="${r.id}">${escape(r.id+' '+r.name+' · '+r.level)}</option>`).join('');if(old)select.value=old;if(!selectedRole)await loadRole();}
    try{const knowledge=await api('/knowledge');const counts=knowledge.counts_by_source_kind;
      document.getElementById('capKnowledge').innerHTML=counts?Object.entries(counts).map(([k,v])=>`<span class="chip">${escape(k)} ${escape(v)}</span>`).join(''):'來源分類 UNKNOWN（舊版 API 尚未提供）';
    }catch(e){document.getElementById('capKnowledge').textContent='知識來源 API 無法驗證：'+e.message;}
  }catch(e){document.getElementById('capSync').textContent='能力 API 尚未就緒：'+e.message;}finally{loading=false;}}
  async function loadRole(){const id=document.getElementById('capRole').value;selectedRole=id;const pack=await api('/roles/'+id);const select=document.getElementById('capSkill');select.innerHTML=pack.required_skills.map(s=>`<option>${escape(s)}</option>`).join('');document.getElementById('capParams').value='';document.getElementById('capOutput').textContent=pack.scope.join('\n');}
  if(page==='workspace'){
    const work=document.createElement('div');work.className='panel';work.innerHTML='<h3>執行專業工程能力</h3><p>選擇角色與方法，載入明確標示的合成案例，或貼上自己的 JSON 工程資料。執行會建立 SQLite Task、Workflow、Evidence 與獨立規則審查。</p><label for="capRole">Capability Seat</label><select id="capRole"></select><label for="capSkill">Executable Skill</label><select id="capSkill"></select><label for="capObjective">Engineering Objective</label><input id="capObjective" placeholder="例如：驗證陣列兩通道的延遲與方向估計"><label for="capSource">資料來源</label><select id="capSource"><option value="USER_SUPPLIED_UNVERIFIED">使用者資料（尚未驗證校正）</option><option value="SYNTHETIC">合成 Golden 案例</option></select><label for="capParams">符合 input schema 的 JSON</label><textarea id="capParams" rows="12" spellcheck="false"></textarea><div class="actions"><button type="button" class="btn" id="capFixture">載入合成 Golden 案例</button><button type="button" class="btn" id="capRun">執行本機分析並建立 Evidence</button></div><pre id="capOutput" aria-live="polite"></pre>';
    const form=document.createElement('div');form.className='formgrid';
    work.insertBefore(form,work.querySelector('label'));
    for(const id of ['capRole','capSkill','capSource','capObjective','capParams']){
      const field=document.createElement('div');field.className=['capObjective','capParams'].includes(id)?'field full':'field';
      field.appendChild(work.querySelector(`label[for="${id}"]`));field.appendChild(work.querySelector('#'+id));form.appendChild(field);
    }
    work.querySelector('#capOutput').className='code';
    section.appendChild(work);
    const intake=document.createElement('button');intake.type='button';intake.className='btn';intake.textContent='用本機 AI 理解工程目標並建議方法';work.querySelector('.actions').prepend(intake);
    intake.onclick=async()=>{intake.disabled=true;try{const description=document.getElementById('capObjective').value.trim();if(!description)throw Error('請先輸入工程目標');const result=await api('/intake',{description,transducer:'Both',lifecycle:'EVT'});document.getElementById('capOutput').textContent=JSON.stringify(result,null,2);}catch(e){showError(e);}finally{intake.disabled=false;}};
    document.getElementById('capRole').onchange=()=>loadRole().catch(showError);
    document.getElementById('capSkill').onchange=()=>{document.getElementById('capParams').value='';};
    document.getElementById('capFixture').onclick=async()=>{try{const role=document.getElementById('capRole').value,skill=document.getElementById('capSkill').value;const data=await api('/fixture/'+role+'?skill='+encodeURIComponent(skill));document.getElementById('capParams').value=JSON.stringify(data.fixture.input,null,2);document.getElementById('capSource').value='SYNTHETIC';document.getElementById('capObjective').value=data.fixture.reason;}catch(e){showError(e);}};
    document.getElementById('capRun').onclick=async()=>{const button=document.getElementById('capRun');button.disabled=true;try{const params=JSON.parse(document.getElementById('capParams').value),objective=document.getElementById('capObjective').value.trim();if(!objective)throw Error('請填寫工程目標');const report=await api('/execute',{role_id:document.getElementById('capRole').value,skill_id:document.getElementById('capSkill').value,params,objective,source_kind:document.getElementById('capSource').value,risk:'R1'});document.getElementById('capOutput').textContent=JSON.stringify({state:report.state,task:report.task_id,workflow:report.workflow_id,evidence:report.evidence_run_id,review:report.review,source:report.source_kind,result:report.numerical_result.values},null,2);await refresh();}catch(e){showError(e);}finally{button.disabled=false;}};
  }
  function showError(e){document.getElementById('capOutput').textContent='未完成：'+e.message;}
  refresh();setInterval(refresh,10000);addEventListener('focus',refresh);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
})();
