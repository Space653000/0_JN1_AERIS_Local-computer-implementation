"""Windows loopback runtime handover; never blindly kill a PID or expose a token."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.aeris'/'state'
TOKEN=STATE/'.supervisor-token'
BASE='http://127.0.0.1:8765'


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    if os.name!='nt' or str(ROOT).lower()!='c:\\0_jn1_aeris': raise RuntimeError('only the authorized Windows root is supported')
    old=read(STATE/'SUPERVISOR.json'); old_token=TOKEN.read_text(encoding='utf-8-sig').strip()
    with urllib.request.urlopen(BASE+'/health',timeout=5) as response: health=json.load(response)
    expected=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if old['implementation_sha']==expected: raise RuntimeError('already current; no replacement needed')
    logs=ROOT/'.aeris'/'logs'; logs.mkdir(exist_ok=True)
    with (logs/('supervisor-'+expected[:10]+'.log')).open('ab') as log:
        child=subprocess.Popen([str(ROOT/'.venv'/'Scripts'/'python.exe'),'-B','-m','aeris_runtime','company','serve','--port','8765'],
                               cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,
                               creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        current=read(STATE/'SUPERVISOR.json')
        if current['pid']!=old['pid'] and current['implementation_sha']==expected: break
        if child.poll() is not None:
            # A failed candidate may have written its token before binding; restore the live predecessor's token.
            TOKEN.write_text(old_token,encoding='utf-8')
            raise RuntimeError('candidate exited; old server retained; inspect local log')
        time.sleep(.2)
    else: raise RuntimeError('candidate readiness not proven; no predecessor shutdown attempted')
    new_token=TOKEN.read_text(encoding='utf-8-sig').strip()
    request=urllib.request.Request(BASE+'/shutdown',method='POST',headers={'X-AERIS-Supervisor-Token':old_token})
    with urllib.request.urlopen(request,timeout=10) as response:
        if not json.load(response).get('shutdown')=='accepted': raise RuntimeError('predecessor did not accept shutdown')
    # Legacy predecessor may remove the shared token when closing. Restore only the candidate's secret.
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen(BASE+'/health',timeout=2) as response: live=json.load(response)
            if live.get('implementation_sha')==expected: break
        except OSError: pass
        time.sleep(.2)
    else: raise RuntimeError('new runtime health not proven; do not report success')
    TOKEN.write_text(new_token,encoding='utf-8'); os.chmod(TOKEN,0o600)
    with urllib.request.urlopen(BASE+'/api/v1/capabilities',timeout=30) as response: matrix=json.load(response)
    if matrix['100_role_L2']!=100: raise RuntimeError('deployed capability matrix failed')
    report={'result':'PASS','old_pid':old['pid'],'new_pid':current['pid'],'implementation_sha':expected,
            '100_role_L2':matrix['100_role_L2'],'authenticated_graceful_shutdown':True,'blind_process_kill':False,
            'local_only':True,'remote_write_performed':False}
    (ROOT/'.aeris'/'evidence'/'professional-runtime-deploy.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__': main()
