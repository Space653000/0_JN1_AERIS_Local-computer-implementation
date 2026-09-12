/* Language/localization: zh-TW is the default source of truth; en.json is a translation overlay. */
(async()=>{
  const LANG_KEY='aeris-lang';
  const getLang=()=>localStorage.getItem(LANG_KEY)==='en'?'en':'zh-TW';
  window.AERIS_LANG=getLang();

  const [zhRes,enRes]=await Promise.all([
    fetch('/assets/zh-TW.json',{cache:'no-store'}),
    fetch('/assets/en.json',{cache:'no-store'}).catch(()=>null),
  ]);
  window.AERIS_I18N=Object.freeze(await zhRes.json());
  window.AERIS_EN=Object.freeze(enRes&&enRes.ok?await enRes.json():{});

  window.aerisText=value=>{
    const source=String(value??'');
    if(getLang()==='en')return source;
    if(window.AERIS_I18N[source])return window.AERIS_I18N[source];
    return source
      .replaceAll('Light Mode','淺色模式').replaceAll('Dark Mode','深色模式')
      .replaceAll('Collapse','收合').replaceAll('Expand','展開')
      .replaceAll('Chief Council','首席架構委員會').replaceAll('Speaker CoE','揚聲器卓越中心')
      .replaceAll('Microphone CoE','麥克風卓越中心').replaceAll('Product Chiefs','產品首席團隊')
      .replaceAll('Distinguished Experts','特聘領域專家').replaceAll('Engineering Ops','工程營運團隊');
  };

  const translated=new WeakSet();
  const translateStaticText=root=>{
    if(getLang()!=='en')return;
    const dict=window.AERIS_EN;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    const nodes=[];
    while(walker.nextNode())nodes.push(walker.currentNode);
    for(const n of nodes){
      if(translated.has(n))continue;
      const raw=n.nodeValue,trimmed=raw.trim();
      if(!trimmed||!dict[trimmed])continue;
      n.nodeValue=raw.replace(trimmed,dict[trimmed]);
      translated.add(n);
    }
    for(const el of root.querySelectorAll?root.querySelectorAll('[placeholder],[title],[aria-label]'):[]){
      for(const attr of ['placeholder','title','aria-label']){
        const v=el.getAttribute(attr);
        if(v&&dict[v])el.setAttribute(attr,dict[v]);
      }
    }
  };

  const localizeUtilities=()=>{
    const theme=document.querySelector('[data-theme-label]');
    const sidebar=document.querySelector('[data-sidebar-label]');
    const lang=getLang();
    const themeText=lang==='en'
      ?(document.documentElement.dataset.theme==='dark'?'Light Mode':'Dark Mode')
      :(document.documentElement.dataset.theme==='dark'?'淺色模式':'深色模式');
    const sidebarText=lang==='en'
      ?(document.documentElement.dataset.sidebar==='collapsed'?'Expand':'Collapse')
      :(document.documentElement.dataset.sidebar==='collapsed'?'展開':'收合');
    if(theme&&theme.textContent!==themeText)theme.textContent=themeText;
    if(sidebar&&sidebar.textContent!==sidebarText)sidebar.textContent=sidebarText;
  };

  const injectLangToggle=()=>{
    const bar=document.querySelector('.sidebar-utilities');
    if(!bar||bar.querySelector('[data-lang-toggle]'))return;
    const btn=document.createElement('button');
    btn.className='utility-btn';
    btn.type='button';
    btn.setAttribute('data-lang-toggle','');
    btn.title=getLang()==='en'?'切換為繁體中文':'Switch to English';
    btn.innerHTML='<span class="nav-icon">文</span><span data-lang-label>'+(getLang()==='en'?'中文':'EN')+'</span>';
    btn.onclick=()=>{
      localStorage.setItem(LANG_KEY,getLang()==='en'?'zh-TW':'en');
      location.reload();
    };
    bar.appendChild(btn);
  };
  const ensureLangToggle=()=>{
    injectLangToggle();
    if(!document.querySelector('.sidebar-utilities')){
      new MutationObserver((_,obs)=>{if(document.querySelector('.sidebar-utilities')){injectLangToggle();obs.disconnect()}})
        .observe(document.documentElement,{subtree:true,childList:true});
    }
  };

  document.addEventListener('DOMContentLoaded',()=>{localizeUtilities();ensureLangToggle();translateStaticText(document.body)});
  if(document.readyState!=='loading'){localizeUtilities();ensureLangToggle();translateStaticText(document.body)}
  document.addEventListener('click',()=>setTimeout(localizeUtilities,0));
  new MutationObserver(muts=>{
    localizeUtilities();
    if(getLang()==='en')for(const m of muts)for(const n of m.addedNodes)if(n.nodeType===1||n.nodeType===3)translateStaticText(n.nodeType===1?n:n.parentNode||document.body);
  }).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
  window.dispatchEvent(new Event('aeris-i18n-ready'));
})().catch(()=>{window.AERIS_I18N=Object.freeze({});window.AERIS_EN=Object.freeze({});window.aerisText=value=>String(value);});
