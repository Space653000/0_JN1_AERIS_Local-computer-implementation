(()=>{
  const REFRESH_MS=10000;
  const ASSET_CHECK_MS=15000;
  const liveRefreshTargets=[loadStatus,loadProjects,loadTasks,loadRoles,loadSkills,loadWorkflows,loadAudit];
  let refreshInFlight=false;
  let assetBaseline=null;

  async function refreshLivePanels(){
    if(refreshInFlight)return;
    refreshInFlight=true;
    try{
      await Promise.allSettled(liveRefreshTargets.map(fn=>fn()));
    }finally{
      refreshInFlight=false;
    }
  }

  async function currentAssetSnapshot(){
    const paths=['/','/assets/app.js','/assets/styles.css','/assets/live-refresh.js'];
    const bodies=await Promise.all(paths.map(async path=>{
      const response=await fetch(path,{cache:'no-store'});
      if(!response.ok)throw new Error(`asset ${path} HTTP ${response.status}`);
      return response.text();
    }));
    return bodies.map(body=>`${body.length}:${body}`).join('\n---AERIS-ASSET---\n');
  }

  async function reloadWhenFrontendChanges(){
    try{
      const snapshot=await currentAssetSnapshot();
      if(assetBaseline===null){
        assetBaseline=snapshot;
        return;
      }
      if(snapshot!==assetBaseline)location.reload();
    }catch(_error){
      // Live API polling remains authoritative; a transient asset check must not break the control plane.
    }
  }

  window.addEventListener('focus',refreshLivePanels);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshLivePanels()});
  setInterval(refreshLivePanels,REFRESH_MS);
  setInterval(reloadWhenFrontendChanges,ASSET_CHECK_MS);
  refreshLivePanels();
  reloadWhenFrontendChanges();
})();
