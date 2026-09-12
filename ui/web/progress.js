async function load(){
  const r=await fetch('/api/v1/progress',{cache:'no-store'}),d=await r.json();
  document.getElementById('state').textContent='已更新 '+new Date(d.generated_at_utc).toLocaleString('zh-TW');
  document.getElementById('overall').textContent='總體 '+d.overall_percent+'%';
  document.getElementById('next').textContent='下一步：'+d.next_action;
  document.getElementById('phases').innerHTML=Object.entries(d.phase_percent).map(([k,v])=>'<div class="card metric"><span>'+k+'</span><strong>'+v+'%</strong></div>').join('');
  document.getElementById('blockers').textContent=d.blockers.length?'阻礙項：'+d.blockers.join('、'):'阻礙項：無';
  document.getElementById('items').innerHTML=d.items.map(x=>'<div class="row"><b>'+x.id+'</b><span>'+x.state+' · '+x.percent+'%</span><small>'+(x.evidence||'無證據')+' · SHA '+(x.sha||'UNKNOWN')+'</small></div>').join('');
}
load();
setInterval(load,10000);
window.addEventListener('focus',load);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
