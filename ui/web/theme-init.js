const requestedTheme=new URLSearchParams(location.search).get('theme');
document.documentElement.dataset.theme=requestedTheme==='light'?'light':'dark';
