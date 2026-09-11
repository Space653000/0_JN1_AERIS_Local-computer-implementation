/* zh-TW presentation source shared by static pages and live API renderers. */
(async()=>{
  const response=await fetch('/assets/zh-TW.json',{cache:'no-store'});
  window.AERIS_I18N=Object.freeze(await response.json());
  window.aerisText=value=>window.AERIS_I18N[String(value)]||String(value);
  window.dispatchEvent(new Event('aeris-i18n-ready'));
})().catch(()=>{window.AERIS_I18N=Object.freeze({});window.aerisText=value=>String(value);});
