"""Read-only upstream verification, independent of private Core cache."""
import json
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aeris_runtime.engineering.canonical_registry import load, validate_source


def main():
    groups=load(ROOT)
    pin=json.loads((ROOT/'core.lock.json').read_text(encoding='utf-8-sig'))['canonical_roles']
    url=f"https://raw.githubusercontent.com/Space653000/0_JN1_AERIS/{pin['core_commit']}/aeris-data.js"
    with urllib.request.urlopen(url,timeout=30) as response:
        data=response.read(2_000_001)
    if len(data)>2_000_000: raise ValueError('Core source exceeds bounded size')
    validate_source(data,pin,groups)
    print(json.dumps({'state':'PINNED_UPSTREAM_SOURCE_MATCH','core_commit':pin['core_commit'],
                      'source_sha256_lf':pin['source_sha256_lf'],'remote_write_performed':False}))


if __name__=='__main__': main()
