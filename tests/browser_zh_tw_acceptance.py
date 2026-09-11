"""Real Chrome visible-text crawl for the local AERIS UI."""
from __future__ import annotations
import html, json, re, subprocess, tempfile, urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8765"
ROUTES = [
    "/", "/dashboard", "/workspace", "/services", "/progress", "/progress-center",
    "/dashboard#activity", "/dashboard#roles", "/dashboard#assets", "/dashboard#trust",
    "/workspace#task", "/workspace#pod", "/workspace#contract",
    "/services#verification", "/services#risk", "/services#evidence", "/services#health",
    "/dashboard?theme=light", "/workspace?theme=light", "/services?theme=light",
]
ALLOW = {"API","SHA","HTTP","JSON","Runtime","Evidence","PASS","BLOCKED","UNKNOWN","Ollama","Git","Python","PowerShell","AERIS","SQLite","Pod","AEC","DOA","FFT","DSP","PDM","ADC","TWS","FR","THD","SNR","STFT","G0","G1","G2","G3","G4","G5"}

def visible_text(dom: str) -> list[str]:
    dom = re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<noscript[^>]*>.*?</noscript>", " ", dom, flags=re.I|re.S)
    dom = re.sub(r"<[^>]+>", " ", dom)
    return [html.unescape(x).strip() for x in re.split(r"[\r\n]+|\s{2,}", dom) if html.unescape(x).strip()]

def violations(texts: list[str]) -> list[str]:
    out=[]
    for t in texts:
        words = re.findall(r"[A-Za-z][A-Za-z0-9_+./-]*", t)
        bad=[w for w in words if len(w)>1 and w not in ALLOW and not re.fullmatch(r"R\d{3}|P[0-6](?:\.\d+)?|v?\d+(?:\.\d+)*",w)]
        if bad: out.append(t)
    return out

def crawl() -> dict:
    rows=[]
    with tempfile.TemporaryDirectory(prefix="aeris-zh-") as td:
        for route in ROUTES:
            out=Path(td)/route.strip("/").replace("/","_")
            cmd=[r"C:\Program Files\Google\Chrome\Application\chrome.exe", "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=3000", f"--user-data-dir={td}/profile", f"--dump-dom", BASE+route]
            p=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=30)
            dom=p.stdout
            texts=visible_text(dom)
            rows.append({"route":route,"exit_code":p.returncode,"visible_strings":len(texts),"violations":violations(texts)})
    return {"routes":rows,"routes_checked":len(rows),"visible_strings_checked":sum(x["visible_strings"] for x in rows),"english_violations":sum(len(x["violations"]) for x in rows),"passed":all(not x["violations"] and x["exit_code"]==0 for x in rows)}

if __name__ == "__main__":
    print(json.dumps(crawl(), ensure_ascii=False, indent=2))
