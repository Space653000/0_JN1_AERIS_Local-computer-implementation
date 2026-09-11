/* zh-TW presentation source shared by static pages and live API renderers. */
(async()=>{
  const response=await fetch('/assets/zh-TW.json',{cache:'no-store'});
  window.AERIS_I18N=Object.freeze(await response.json());
  window.aerisText=value=>{
    const source=String(value??'');
    if(window.AERIS_I18N[source])return window.AERIS_I18N[source];
    return source
      .replaceAll('Light Mode','淺色模式').replaceAll('Dark Mode','深色模式')
      .replaceAll('Collapse','收合').replaceAll('Expand','展開')
      .replaceAll('Chief Council','首席架構委員會').replaceAll('Speaker CoE','揚聲器卓越中心')
      .replaceAll('Microphone CoE','麥克風卓越中心').replaceAll('Product Chiefs','產品首席團隊')
      .replaceAll('Distinguished Experts','特聘領域專家').replaceAll('Engineering Ops','工程營運團隊');
  };
  const localizeUtilities=()=>{
    const theme=document.querySelector('[data-theme-label]');
    const sidebar=document.querySelector('[data-sidebar-label]');
    const themeText=document.documentElement.dataset.theme==='dark'?'淺色模式':'深色模式';
    const sidebarText=document.documentElement.dataset.sidebar==='collapsed'?'展開':'收合';
    if(theme&&theme.textContent!==themeText)theme.textContent=themeText;
    if(sidebar&&sidebar.textContent!==sidebarText)sidebar.textContent=sidebarText;
  };
  document.addEventListener('DOMContentLoaded',localizeUtilities);
  document.addEventListener('click',()=>setTimeout(localizeUtilities,0));
  new MutationObserver(localizeUtilities).observe(document.documentElement,{subtree:true,childList:true});
  window.dispatchEvent(new Event('aeris-i18n-ready'));
})().catch(()=>{window.AERIS_I18N=Object.freeze({});window.aerisText=value=>String(value);});
